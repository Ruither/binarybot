# Módulo principal para executar o robô com base nos módulos importados

from mt5_collector import initialize_mt5, shutdown_mt5, get_rates
from support_resistance import calculate_support_resistance
from lateralization import is_lateralization
from patterns import check_retracement, check_previous_wicks, is_candle_stretched
from signals import evaluate_entry, check_signal_success
from telegram_notifier import send_telegram_message
import time
from datetime import datetime, timedelta, timezone
from investing_news import buscar_noticias_importantes, dentro_de_janela_de_noticia

# Carrega configurações externas do arquivo YAML com validação
import yaml, os, sys
config_path = os.path.join(os.path.dirname(__file__), "config.yaml")

try:
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

        # Verificação de campos obrigatórios no config.yaml
        required_keys = [
            "symbols", "min_distance_pips", "min_retracement_percent",
            "tempo_analise_segundos", "horario_operacao", "telegram"
        ]

        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            print(f"O arquivo de configuração está incompleto. Faltando: {', '.join(missing_keys)}")
            sys.exit(1)

        # Verifica subchaves do bloco 'telegram'
        if not all(k in config["telegram"] for k in ("bot_token", "chat_id")):
            print("O bloco 'telegram' deve conter as chaves 'bot_token' e 'chat_id'.")
            sys.exit(1)

        # Verifica subchaves do bloco 'horario_operacao'
        if not all(k in config["horario_operacao"] for k in ("inicio", "fim")):
            print("O bloco 'horario_operacao' deve conter as chaves 'inicio' e 'fim'.")
            sys.exit(1)

except FileNotFoundError:
    print(f"Arquivo de configuração não encontrado em: {config_path}")
    sys.exit(1)

except yaml.YAMLError as e:
    print("Erro ao interpretar o arquivo YAML:", e)
    sys.exit(1)

# Parâmetros de suporte e resistência
sr_config = config.get("support_resistance", {})
min_touches = sr_config.get("min_touches", 2)
min_distance_between_touches = sr_config.get("min_distance_between_touches", 5)
tolerance_pips = sr_config.get("tolerance_pips", 2)
min_region_separation = sr_config.get("min_region_separation", 10)

# Lista de pares de moedas definida no arquivo de configuração
symbols = config["symbols"]

# Token e ID do chat para envio no Telegram
bot_token = config["telegram"]["bot_token"]
chat_id = config["telegram"]["chat_id"]

# Distância mínima entre o preço de abertura e o nível de suporte/resistência
min_distance_pips = config["min_distance_pips"]

# Percentual mínimo de retração da vela
min_retr_pct = config["min_retracement_percent"]

# Janela de tempo da análise (em segundos)
tempo_analise = config["tempo_analise_segundos"]

# Horário de operação permitido
hora_inicio = config["horario_operacao"]["inicio"]
hora_fim = config["horario_operacao"]["fim"]

def main():
    # Inicializa conexão com MetaTrader 5
    if not initialize_mt5():
        return
    
    # 🔎 Carrega notícias importantes do dia
    eventos_importantes = buscar_noticias_importantes()
    if eventos_importantes is None or len(eventos_importantes) == 0:
        print("Nenhuma notícia importante carregada. Operando sem bloqueio.")

    last_news_update = time.time()  # para atualizar a cada 1 hora

    # Dicionário que armazena sinais enviados e dados relacionados
    signals = {}

    # Contadores para estatísticas
    total_signals = 0
    success_signals = 0
    failed_signals = 0

    # Dicionário de controle de retração por símbolo
    retracement_data = {
        symbol: {'has_retraced': False, 'body_size': 0} for symbol in symbols
    }

    print("Robô iniciado. Aguardando vela M5...")

    try:
        while True:
            current_time = time.localtime()
            hour = current_time.tm_hour
            day = datetime.now().weekday()  # Dia da semana (0=segunda)

            # ⏳ Atualiza as notícias a cada 1 hora
            if time.time() - last_news_update > 3600:
                print("Atualizando eventos econômicos...")
                eventos_importantes = buscar_noticias_importantes()
                last_news_update = time.time()
                if eventos_importantes is None or len(eventos_importantes) == 0:
                    print("Atualização de notícias falhou. Continuando operação sem bloqueio.")
                else:
                    print(f"{len(eventos_importantes)} notícias de impacto carregadas.")

            # Valida se está dentro do horário de operação: dias úteis das 6h às 17h
            if 0 <= day <= 4 and hora_inicio <= hour < hora_fim:
                # Aguarda até o próximo múltiplo de 5 minutos
                if current_time.tm_min % 5 != 0:
                    wait_time = (5 - current_time.tm_min % 5) * 60 - current_time.tm_sec
                    time.sleep(wait_time)

                # Início da janela de 2 minutos de análise (tempo_analise configurado no YAML)
                start_time = time.time()
                while time.time() - start_time < tempo_analise:
                    #print(f"Analisando ativos às {datetime.now().strftime('%H:%M:%S')}...")

                    # Verifica se há alguma notícia de alto impacto no momento
                    now = datetime.now()
                    bloqueado = False

                    for evento in eventos_importantes:
                        janela_inicio = evento['horario'] - timedelta(minutes=15)
                        janela_fim = evento['horario'] + timedelta(minutes=15)

                        if janela_inicio <= now <= janela_fim:
                            print(f"Sinal bloqueado por notícia: {evento['horario'].strftime('%H:%M')} - {evento['moeda']} - {evento['descricao']} ({evento['impacto']} estrelas)")
                            bloqueado = True
                            break

                    if bloqueado:
                        continue

                    for symbol in symbols:
                        # Coleta 37 velas M5 (36 anteriores + atual)
                        rates = get_rates(symbol, 5, 0, 100)
                        if rates is None or len(rates) < 37:
                            continue

                        current = rates[-1]
                        high = current['high']
                        low = current['low']
                        open_ = current['open']
                        close = current['close']

                        # Calcula tamanho do corpo da vela
                        body_size = abs(close - open_)
                        retracement_data[symbol]['body_size'] = body_size

                        # Verifica retração mínima
                        if body_size > 0.00001:
                            retr_up = (high - close) / body_size
                            retr_down = (close - low) / body_size
                            if retr_up >= min_retr_pct or retr_down >= min_retr_pct:
                                retracement_data[symbol]['has_retraced'] = True

                        # Suporte e resistência com as 24 velas (ignorando 12 mais recentes)
                        support, resistance = calculate_support_resistance(
                            rates,
                            symbol,
                            min_touches=min_touches,
                            min_distance_between_touches=min_distance_between_touches,
                            tolerance_pips=tolerance_pips,
                            min_region_separation=min_region_separation
                        )
                        if support is None or resistance is None:
                            print(f"{symbol} Suporte ou resistência não encontrado.")
                            continue

                        # Verifica lateralização nas últimas 36 velas
                        if not is_lateralization(rates[-36:]):
                            print(f"{symbol} Gráfico não está lateralizado.")
                            continue

                        # Avalia sinal técnico
                        signal = evaluate_entry(rates, support, resistance, symbol, min_distance_pips, retracement_data)

                        # Se houver sinal, checa pavios e vela esticada se necessário
                        if signal:
                            direction = "buy" if "buy" in signal else "sell"
                            if not check_previous_wicks(rates, direction):
                                continue

                            minuto = now.minute
                            if minuto % 15 >= 10:
                                m15_rates = get_rates(symbol, 15, 1, 1)
                                if not m15_rates or not is_candle_stretched(m15_rates[0]):
                                    continue
                            if minuto % 30 >= 20:
                                m30_rates = get_rates(symbol, 30, 1, 1)
                                if not m30_rates or not is_candle_stretched(m30_rates[0]):
                                    continue
                            if minuto >= 40:
                                h1_rates = get_rates(symbol, 60, 1, 1)
                                if not h1_rates or not is_candle_stretched(h1_rates[0]):
                                    continue

                        # Se for um novo sinal, envia ao Telegram e registra
                        if signal and symbol not in signals:
                            total_signals += 1
                            entry_price = current['close']
                            now_str = datetime.now().strftime("%H:%M:%S")
                            price_fmt = "{:.3f}" if "JPY" in symbol else "{:.5f}"
                            formatted_price = price_fmt.format(entry_price)

                            message = (
                                f"<b>NEW Time:</b> <code>{now_str} 🕐</code>\n"
                                f"<b>Symbol:</b> <code>{symbol} 📊</code>\n"
                                f"<b>Signal:</b> <code>{signal}</code>\n"
                                f"<b>Price:</b> <code>{formatted_price} 💰</code>"
                            )
                            print(message)
                            send_telegram_message(bot_token, chat_id, message)

                            signals[symbol] = {
                                'signal': signal,
                                'entry_price': entry_price,
                                'timestamp': now_str
                            }

                        # 🔍 Imprime sempre as distâncias para debug, mesmo que tenha sinal
                        pips_multiplier = 0.01 if "JPY" in symbol else 0.0001
                        current_open = current['open']
                        distance_to_support = (current_open - support) / pips_multiplier
                        distance_to_resistance = (resistance - current_open) / pips_multiplier
                        distance_to_support = max(0, distance_to_support)
                        distance_to_resistance = max(0, distance_to_resistance)

                        now_str = datetime.now().strftime("%H:%M:%S")
                        print(f"{now_str} - Waiting for best entry. {symbol} - Sup: {support:.5f}, Resist: {resistance:.5f}, DS: {distance_to_support:.2f}, DR: {distance_to_resistance:.2f}")
                
                # Aguarda início da nova vela M5 para validar sinais
                while True:
                    current_time = time.localtime()
                    if current_time.tm_sec == 0 and current_time.tm_min % 5 == 0:
                        # Reseta os dados de retração para nova análise
                        for symbol in symbols:
                            retracement_data[symbol]['has_retraced'] = False
                            retracement_data[symbol]['body_size'] = 0
                        break
                    time.sleep(1)

                # Avalia os resultados dos sinais emitidos
                for symbol, data in list(signals.items()):
                    final = get_rates(symbol, 5, 0, 1)  # Coleta a vela recém-fechada
                    if not final:
                        continue
                    final_price = final[-1]['close']

                    # Formata o preço de saída
                    price_fmt = "{:.3f}" if "JPY" in symbol else "{:.5f}"
                    formatted_price = price_fmt.format(final_price)

                    # Verifica se o movimento foi na direção esperada
                    success = check_signal_success(data['signal'], final_price, data['entry_price'])
                    if success:
                        success_signals += 1
                        result = "NEW Successful ✅"
                    else:
                        failed_signals += 1
                        result = "NEW Failed ❌"

                    # Monta mensagem com resultado e histórico
                    result_msg = (
                        f"<b>NEW Symbol:</b> <code>{symbol} 📊</code>\n"
                        f"<b>Price:</b> <code>{formatted_price} 💰</code>\n"
                        f"<b>Resultado:</b> <code>{result}</code>\n\n"
                        f"<b>Histórico:</b>\n"
                        f"<b>Total:</b> <code>{total_signals}</code>\n"
                        f"<b>Successful:</b> <code>{success_signals} ✅</code>\n"
                        f"<b>Failure:</b> <code>{failed_signals} ❌</code>"
                    )
                    print(result_msg)
                    send_telegram_message(bot_token, chat_id, result_msg)
                    del signals[symbol]  # Remove o sinal já avaliado

            else:
                # Fora do horário de operação, aguarda 5 minutos antes de checar novamente
                print("Fora do horário de operação. Aguardando próxima janela...")
                time.sleep(300)

    finally:
        # Encerra conexão com MetaTrader 5 ao sair do loop
        shutdown_mt5()

# Executa o robô
if __name__ == "__main__":
    main()