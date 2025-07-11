# Contém a lógica para avaliar entrada de sinais e verificar se foram bem-sucedidos

def evaluate_entry(rates, support, resistance, symbol, min_distance_pips, retracement_data):
    # Verifica se o par está presente no dicionário de retração. Se não estiver, inicializa.
    if symbol not in retracement_data:
        retracement_data[symbol] = {'has_retraced': False, 'body_size': 0}

    # Recupera se houve retração previamente registrada
    has_retraced = retracement_data[symbol]['has_retraced']

    # Obtém os dados da última vela
    current = rates[-1]  # Última vela M5
    open_price = current['open']  # Preço de abertura da vela atual
    close_price = current['close']  # Preço de fechamento da vela atual
    time_pos = current['time'] % 300  # Calcula em que segundo da vela M5 estamos (0 a 299)

    # Define o multiplicador de pips com base no par (JPY ou não)
    pips_multiplier = 0.01 if "JPY" in symbol else 0.0001

    # Calcula a distância entre o preço de abertura e o suporte/resistência em pips
    dist_support = abs(open_price - support) / pips_multiplier
    dist_resist = abs(resistance - open_price) / pips_multiplier

    # Verifica se o preço está entre suporte e resistência E ainda dentro dos primeiros 2 minutos da vela M5
    if support < open_price < resistance and time_pos < 120:
        # Condição para compra: preço toca no suporte, houve retração, distância válida
        if close_price == support and has_retraced and dist_support >= min_distance_pips:
            return "buy ⬆️"
        # Condição para venda: preço toca na resistência, houve retração, distância válida
        elif close_price == resistance and has_retraced and dist_resist >= min_distance_pips:
            return "sell ⬇️"

    # Caso nenhuma condição seja satisfeita, não retorna sinal
    return None

def check_signal_success(signal, current_price, previous_price):
    """
    Verifica se o sinal de compra ou venda foi bem-sucedido.
    :param signal: Direção do sinal ('buy ⬆️' ou 'sell ⬇️')
    :param current_price: Preço atual (após a vela seguinte)
    :param previous_price: Preço de entrada (momento do sinal)
    :return: True se o movimento foi na direção correta, False caso contrário
    """
    if signal == "buy ⬆️":
        return current_price > previous_price  # Sucesso se o preço subiu após entrada
    elif signal == "sell ⬇️":
        return current_price < previous_price  # Sucesso se o preço caiu após entrada
    return False  # Se o tipo de sinal não for reconhecido