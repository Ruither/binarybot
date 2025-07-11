# === support_resistance.py ===
# Módulo responsável por calcular os níveis de Suporte e Resistência com base em:
# - Número mínimo de toques (min_touches)
# - Distância mínima entre os toques (min_distance_between_touches)
# - Agrupamento por faixa de preço (tolerance_pips)
# - Validação de que os toques estão em regiões temporais diferentes (min_region_separation)

def calculate_support_resistance(rates, symbol, min_touches=2, min_distance_between_touches=5, tolerance_pips=2, min_region_separation=10):
    """
    Calcula níveis de Suporte e Resistência com validação por múltiplos toques em regiões separadas.

    :param rates: Lista de candles históricos (esperado pelo menos 73 candles)
    :param symbol: Par de moedas (ex: "GBPJPY")
    :param min_touches: Mínimo de toques exigido por faixa (default: 2)
    :param min_distance_between_touches: Mínimo de velas entre toques consecutivos (default: 5)
    :param tolerance_pips: Tolerância em pips para agrupar preços próximos (default: 2)
    :param min_region_separation: Distância mínima em velas entre regiões de toque (default: 10)
    :return: Tupla (suporte, resistência) ou (None, None) se nenhum nível for válido
    """

    # Proteção contra dados insuficientes
    if len(rates) < 73:
        return None, None

    # Ignora as 6 velas mais recentes (para não pegar níveis influenciados pela ação atual)
    relevant_rates = rates[:-6]

    # Define o multiplicador para conversão de pips para preço real
    pips_multiplier = 0.01 if "JPY" in symbol else 0.0001

    # Converte tolerância de pips para valor real de preço
    tolerance = tolerance_pips * pips_multiplier

    # Função auxiliar para agrupar os índices dos candles por faixa de preço
    def agrupar_por_toques(precos):
        bins = {}
        for idx, price in enumerate(precos):
            # Arredonda o preço para o bin usando a tolerância
            bin_key = round(price / tolerance) * tolerance
            if bin_key not in bins:
                bins[bin_key] = []
            bins[bin_key].append(idx)  # Salva o índice do candle
        return bins

    # Função auxiliar que valida se os toques ocorreram em regiões separadas
    def validar_nivel(indices):
        """
        Retorna True se os índices contêm pelo menos dois grupos de toques
        com separação mínima de min_region_separation velas entre eles.
        """
        if len(indices) < min_touches:
            return False

        # Agrupa os índices com base em distância mínima entre toques
        grupos = [[indices[0]]]
        for idx in indices[1:]:
            if idx - grupos[-1][-1] >= min_distance_between_touches:
                grupos.append([idx])
            else:
                grupos[-1].append(idx)

        # Verifica se há pelo menos dois grupos separados suficientemente
        if len(grupos) >= 2:
            for i in range(len(grupos)):
                for j in range(i + 1, len(grupos)):
                    if abs(grupos[j][0] - grupos[i][-1]) >= min_region_separation:
                        return True
        return False

    # === SUPORTE ===
    lows = [candle['low'] for candle in relevant_rates]
    low_bins = agrupar_por_toques(lows)

    valid_supports = [
        price for price, idxs in low_bins.items()
        if validar_nivel(sorted(idxs))
    ]

    # === RESISTÊNCIA ===
    highs = [candle['high'] for candle in relevant_rates]
    high_bins = agrupar_por_toques(highs)

    valid_resistances = [
        price for price, idxs in high_bins.items()
        if validar_nivel(sorted(idxs))
    ]

    # Se nenhum nível válido foi encontrado
    if not valid_supports or not valid_resistances:
        return None, None

    # Retorna o menor suporte e maior resistência válidos
    return min(valid_supports), max(valid_resistances)
