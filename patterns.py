# Contém funções para analisar retrações e pavios de velas

def check_retracement(candle, min_percent=0.2):
    """
    Verifica se o candle atual apresentou retração suficiente antes de tocar suporte ou resistência.
    A retração é definida como a diferença entre o corpo da vela e sua sombra.
    
    :param candle: Dicionário com dados da vela atual (open, close, high, low)
    :param min_percent: Valor mínimo proporcional para considerar como retração (ex: 0.2 = 20%)
    :return: True se houve retração significativa, False caso contrário
    """
    body = abs(candle['close'] - candle['open'])
    if body == 0:
        return False
    retracement_up = (candle['high'] - candle['close']) / body
    retracement_down = (candle['close'] - candle['low']) / body
    return retracement_up >= min_percent or retracement_down >= min_percent


def check_previous_wicks(rates, direction):
    """
    Verifica se as duas velas anteriores deixaram pavios no lado correto da direção esperada.
    Ex: pavio inferior em suporte (compra), pavio superior em resistência (venda)
    
    :param rates: Lista de candles (esperado pelo menos 3 candles)
    :param direction: 'buy' ou 'sell' indicando a direção do sinal avaliado
    :return: True se ambas velas anteriores tiverem pavios consistentes com a direção, False caso contrário
    """
    prev1 = rates[-2]
    prev2 = rates[-3]

    def wick_valid(candle, direction):
        open_, close = candle['open'], candle['close']
        body = abs(close - open_)

        if body == 0:
            return False

        upper_wick = candle['high'] - max(open_, close)
        lower_wick = min(open_, close) - candle['low']

        if direction == "buy":
            return lower_wick >= 0.20 * body and upper_wick <= 0.40 * body
        elif direction == "sell":
            return upper_wick >= 0.20 * body and lower_wick <= 0.40 * body
        else:
            return False

    return wick_valid(prev1, direction) and wick_valid(prev2, direction)

def is_candle_stretched(candle):
    """
    Determina se uma vela está esticada com base na proporção entre corpo e amplitude total.
    Uma vela esticada é aquela com corpo dominante e pouco pavio no sentido contrário.
    """
    body = abs(candle['close'] - candle['open'])
    total_range = candle['high'] - candle['low']
    if total_range == 0:
        return False
    return body / total_range >= 0.7