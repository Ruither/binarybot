import MetaTrader5 as mt5
import time
import requests
from colorama import init
from datetime import datetime, timedelta
from datetime import datetime

# Inicializar o colorama
init()

# Função para enviar mensagens ao Telegram
def send_telegram_message(bot_token, chat_id, message):
    """
    Envia uma mensagem para um grupo do Telegram usando o bot.
    :param bot_token: Token do bot do Telegram
    :param chat_id: ID do chat do grupo
    :param message: Mensagem a ser enviada
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print(f"Falha ao enviar mensagem: {response.text}")
    except Exception as e:
        print(f"Erro ao enviar mensagem para o Telegram: {e}")

# Função para calcular suporte e resistência com base nas últimas 24 velas M5, ignorando as 12 primeiras
def calculate_support_resistance(symbol):
    """
    Calcula os níveis de suporte e resistência com base nas últimas 24 velas M5, ignorando as últimas 12.
    :param symbol: Par de moeda
    :return: Valor do suporte e resistência.
    """
    rates_m5 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 12, 24)  # Ignorar as últimas 12 velas, considerar as 24 anteriores
    if len(rates_m5) < 24:
        print(f"Dados insuficientes para cálculo de suporte e resistência para {symbol}")
        return None, None

    highs = [rate['high'] for rate in rates_m5]
    lows = [rate['low'] for rate in rates_m5]
    resistance = max(highs)
    support = min(lows)
    return support, resistance

# Função para verificar se o gráfico está em lateralização
def is_lateralization(rates):
    """
    Verifica se o gráfico está em lateralização com base nas últimas 36 velas M5.
    :param rates: Dados das últimas 36 velas M5
    :return: True se estiver em lateralização, False caso contrário.
    """
    if len(rates) < 36:
        return False

    # Calcula os tamanhos das velas (diferença entre abertura e fechamento)
    sizes = [abs(rate['close'] - rate['open']) for rate in rates]
    avg_size = sum(sizes) / len(sizes)

    # Verifica se todos os tamanhos de velas estão dentro de 50% acima ou abaixo da média
    for size in sizes:
        if size < avg_size * 0.5 and size > avg_size * 1.5:
            return False
    return True

# Função para avaliar entrada de compra ou venda
def evaluate_entry(rates, support, resistance, symbol, min_distance_pips,retracement_data):
    """
    Avalia se a entrada de compra ou venda deve ser feita.
    :param rates: Dados das velas M5
    :param support: Nível de suporte
    :param resistance: Nível de resistência
    :param symbol: Par de moeda
    :param min_distance_pips: Distância mínima em pips da abertura da vela até o suporte ou resistência.
    :param retracement_data: Dados de retração para verificar se houve uma retração antes do toque
    :return: Sinal de entrada ('buy' para suporte, 'sell' para resistência, None caso contrário)
    """

    # Garantir que o símbolo esteja no dicionário retracement_data
    if symbol not in retracement_data:
        retracement_data[symbol] = {'has_retraced': False, 'body_size': 0}

    has_retraced_before_touch = retracement_data[symbol]['has_retraced']
    current_open_price = rates[-1]['open']
    current_price = rates[-1]['close']
    current_time = rates[-1]['time']

    # Verifica se as duas velas anteriores deixaram pavios longos
    prev1_wick = abs(rates[-2]['high'] - rates[-2]['close']) > abs(rates[-2]['open'] - rates[-2]['close']) * 0.2
    prev2_wick = abs(rates[-3]['high'] - rates[-3]['close']) > abs(rates[-3]['open'] - rates[-3]['close']) * 0.2

    # Calcula a distância mínima aceitável da abertura da vela para suporte/resistência em pips
    pips_multiplier = 0.01 if "JPY" in symbol else 0.0001
    distance_to_support_pips = abs(current_open_price - support) / pips_multiplier
    distance_to_resistance_pips = abs(resistance - current_open_price) / pips_multiplier

    # Verifica se o preço de abertura da vela atual está entre o suporte e resistência
    if current_open_price > support and current_open_price < resistance:
        # Verifica se a vela atual tocou no suporte ou resistência nos 2 primeiros minutos
        if current_time % 300 < 120:
            if current_price == support and prev1_wick and prev2_wick and distance_to_support_pips >= min_distance_pips and has_retraced_before_touch:
                return "buy ⬆️"
            elif current_price == resistance and prev1_wick and prev2_wick and distance_to_resistance_pips >= min_distance_pips and has_retraced_before_touch:
                return "sell ⬇️"
    return None

# Função para verificar se o sinal foi bem-sucedido
def check_signal_success(signal, current_price, previous_price):
    """
    Verifica se o sinal de compra ou venda foi bem-sucedido.
    :param signal: Sinal de entrada ('buy' ou 'sell')
    :param current_price: Preço atual
    :param previous_price: Preço no momento do sinal
    :return: True se bem-sucedido, False caso contrário.
    """
    if signal == "buy ⬆️":
        return current_price > previous_price
    elif signal == "sell ⬇️":
        return current_price < previous_price
    return False

# Conectar ao MetaTrader 5
if not mt5.initialize():
    print("Falha ao inicializar")
    mt5.shutdown()

# Lista de pares de moedas
symbols = ["EURUSD","EURJPY","EURGBP","USDJPY","GBPUSD","GBPJPY","AUDCHF","USDCAD","NZDJPY","NZDCAD","EURAUD","EURNZD","GBPAUD","GBPCHF","AUDJPY","EURCAD","GBPCAD","CADCHF","GBPNZD","AUDCAD"]

# Token do bot do Telegram e ID do chat do grupo
bot_token = "7471361525:AAEYh_Mmn4R_hzz9hnMDo5RWAJ6VpiCxaPY"
chat_id = "-1002235190703"

# Variáveis de histórico
total_signals = 0
success_signals = 0
failed_signals = 0

# Definir a distância mínima em pips para a validação adicional
min_distance_pips = 3  # Exemplo: 3 pips

# Função principal para coleta de dados em tempo real e análise
def main():
    global total_signals, success_signals, failed_signals

    signals = {}  # Dicionário para armazenar sinais
    retracement_data = {
        symbol: {
            'has_retraced': False,
            'body_size': 0
        }
        for symbol in symbols
    }  # Dados de retração para cada símbolo

    while True:
        current_time = time.localtime()
        minutes = current_time.tm_min
        hour = current_time.tm_hour
        agora = datetime.now()  # Pega a data e hora atuais
        dia_semana = agora.weekday()  # Extrai o dia da semana (0 = segunda, 6 = domingo)

        # Verificar se estamos dentro do horário de negociação (06h às 17h)
        if 0 <= dia_semana <= 4 and 6 <= hour < 17:
            minutes = current_time.tm_min

            # Esperar até o próximo múltiplo de 5 minutos
            if minutes % 5 != 0:
                wait_time = (5 - minutes % 5) * 60 - current_time.tm_sec
                time.sleep(wait_time)

            # Iniciar o ciclo de análise de 2 minutos
            start_time = time.time()
            while time.time() - start_time < 120:  # Executar por 2 minutos
                for symbol in symbols:

                    # Garantir que o símbolo está no retracement_data
                    if symbol not in retracement_data:
                        retracement_data[symbol] = {'has_retraced': False, 'body_size': 0}

                    # Coletar dados de velas M5
                    rates_m5 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 37)  # 37 para incluir a vela atual
                    current_price = rates_m5[-1]['close']

                    # Atualizar os dados de retração
                    if not retracement_data[symbol]['has_retraced']:
                        # Verificar se o preço já se afastou do suporte ou resistência antes de voltar
                        high = rates_m5[-1]['high']
                        current_open = rates_m5[-1]['open']
                        current_close = rates_m5[-1]['close']
                        current_high = rates_m5[-1]['high']
                        current_low = rates_m5[-1]['low']
                    
                    # Calcular o tamanho do corpo da vela
                    body_size = abs(current_close - current_open)
                    retracement_data[symbol]['body_size'] = body_size

                    # Verificar retração com base no corpo da vela
                    if body_size > 0.00001:
                        min_retraction_percent = 0.2  # Exigir 20% de retração
                        retracement_up = (current_high - current_close) / body_size
                        retracement_down = (current_close - current_low) / body_size

                        if retracement_up >= min_retraction_percent or retracement_down >= min_retraction_percent:
                            retracement_data[symbol]['has_retraced'] = True

                    # Calcular suporte e resistência com base nas últimas 24 velas M5 ignorando as últimas 12
                    support, resistance = calculate_support_resistance(symbol)

                    if support is None or resistance is None:
                        continue

                    # Verificar se o gráfico está em lateralização
                    if not is_lateralization(rates_m5[-36:]):  # As últimas 36 velas
                        print(f"{symbol} - Gráfico não está em lateralização. Aguardando melhor entrada.")
                        continue

                    # Avaliar entrada com a nova regra de distância mínima
                    signal = evaluate_entry(rates_m5, support, resistance, symbol, min_distance_pips,  retracement_data[symbol])

                    # Imprimir o momento de entrada e o sinal
                    current_time_str = time.strftime("%H:%M:%S")  # Formata o tempo atual para uma string HH:MM:SS
                    if signal and symbol not in signals:  # Envia apenas um sinal por par de moeda
                        total_signals += 1  # Incrementa o total de sinais
                        previous_price = rates_m5[-1]['close']  # Pega o preço de fechamento da última vela
                        next_candle_time = (current_time.tm_min // 5 + 1) * 5 % 60  # Calcula o tempo da próxima vela M5

                        # Armazena o sinal no dicionário
                        signals[symbol] = {
                            'signal': signal,
                            'previous_price': previous_price,
                            'timestamp': current_time_str,
                            'next_candle_time': next_candle_time  # Armazena o tempo da próxima vela M5
                        }

                        # Formatar preço para envio no Telegram
                        price_format = "{:.3f}" if "JPY" in symbol else "{:.5f}"
                        formatted_price = price_format.format(previous_price)

                        # Cria a mensagem para imprimir e enviar para o Telegram
                        message = (
                            f"<b>Time:</b> <code>{current_time_str} 🕐</code>\n"
                            f"<b>Symbol:</b> <code>{symbol} 📊</code>\n"
                            f"<b>Signal:</b> <code>{signal}</code>\n"
                            f"<b>Price:</b> <code>{formatted_price} 💰</code>"
                        )
                        print(message)
                        try:
                            send_telegram_message(bot_token, chat_id, message)
                        except Exception as e:
                             print(f"Erro ao enviar mensagem para o Telegram: {e}")
                    else:
                        #Calcula as distâncias para suporte e resistência
                        pips_multiplier = 0.01 if "JPY" in symbol else 0.0001
                        distance_to_support = (rates_m5[-1]['open'] - support) / pips_multiplier
                        distance_to_resistance = (resistance - rates_m5[-1]['open']) / pips_multiplier

                        #Imprime uma mensagem de espera com as distâncias
                        print(f"{current_time_str} - Waiting for best entry. {symbol} - Sup: {support}, Resist: {resistance}, DS: {distance_to_support:.2f}, DR: {distance_to_resistance:.2f}")
                    
            
            # Esperar nova vela M5 e reinicializar dados de retração
            while True:
                current_time = time.localtime()
                if current_time.tm_sec == 0 and current_time.tm_min % 5 == 0:
                    for symbol in symbols:
                        retracement_data[symbol]['has_retraced'] = False
                        retracement_data[symbol]['body_size'] = 0
                    break
                time.sleep(1)

            # Verifica o resultado dos sinais após o início da nova vela M5
            for symbol, data in list(signals.items()):  # Itera sobre uma cópia dos itens do dicionário de sinais
                new_rates_m5 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 1)  # Pega a última vela M5
                current_price = new_rates_m5[-1]['close']  # Pega o preço de fechamento da última vela

                # Formatar preços
                price_format = "{:.3f}" if "JPY" in symbol else "{:.5f}"
                formatted_price = price_format.format(current_price)

                # Verifica se o sinal foi bem-sucedido
                success = check_signal_success(data['signal'], current_price, data['previous_price'])
                if success:
                    success_signals += 1  # Incrementa o contador de sinais bem-sucedidos
                    success_message = "Successful ✅"
                else:
                    failed_signals += 1  # Incrementa o contador de sinais falhos
                    success_message = "Failed ❌"

                # Cria a mensagem com o resultado e histórico
                message = (
                    f"<b>Symbol:</b> <code>{symbol} 📊</code>\n"
                    f"<b>Price:</b> <code>{formatted_price} 💰</code>\n"
                    f"<b>Resultado:</b> <code>{success_message}</code>\n\n"
                    f"<b>Histórico:</b>\n"
                    f"<b>Total:</b> <code>{total_signals}</code>\n"
                    f"<b>Successful:</b> <code>{success_signals} ✅</code>\n"
                    f"<b>Failure:</b> <code>{failed_signals} ❌</code>"
                )
                print(message)
                try:
                    send_telegram_message(bot_token, chat_id, message)  # Envia a mensagem para o Telegram
                except Exception as e:
                             print(f"Erro ao enviar mensagem para o Telegram: {e}")

                # Remove o sinal verificado do dicionário
                del signals[symbol]
                retracement_data[symbol]['has_retraced'] = False

        else: 
            print("Fora do horário de operação: Segunda a Sexta, das 06h às 17h. Aguardando...")
            time.sleep(3600)  # Aguarda 1 hora antes de verificar o horário novamente

        # Espera até o próximo ciclo de 5 minutos
        time.sleep(1)

# Iniciar a função principal
main()

# Desconectar do MetaTrader 5
mt5.shutdown()