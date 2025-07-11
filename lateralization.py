# Verifica se o gráfico está lateralizado com base na variação dos candles

# :param rates: Lista de candles
# :return: True se estiver lateralizado, False caso contrário
def is_lateralization(rates):
    if len(rates) < 36:
        return False
    # Calcula o tamanho de cada candle
    sizes = [abs(r['close'] - r['open']) for r in rates]
    avg_size = sum(sizes) / len(sizes)  # Média dos tamanhos
    for size in sizes:
        # Verifica se está fora da faixa de variação esperada
        if size < avg_size * 0.5 and size > avg_size * 1.5:
            return False
    return True