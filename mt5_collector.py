# Contém as funções de inicialização, finalização e coleta de dados do MetaTrader 5

import MetaTrader5 as mt5
# Inicializa a conexão com o MetaTrader 5
# :return: True se a conexão for bem-sucedida, False caso contrário
def initialize_mt5():
    if not mt5.initialize():
        print("❌ Erro ao inicializar MetaTrader 5:", mt5.last_error())
        return False
    print("✅ Conectado ao MetaTrader 5 com sucesso.")
    return True

# Finaliza/desconecta a instância ativa do MetaTrader 5
def shutdown_mt5():
    mt5.shutdown()  # Encerra a conexão com o MT5 corretamente

# Coleta os candles históricos a partir de uma posição específica
# :param symbol: Par de moedas (ex: EURUSD)
# :param timeframe: Timeframe do candle (ex: mt5.TIMEFRAME_M5)
# :param start_pos: A partir de qual vela começar a buscar
# :param count: Quantidade de velas desejadas
# :return: Lista de dicionários com OHLC, time, tick_volume, etc
def get_rates(symbol, timeframe, start_pos, count):
    return mt5.copy_rates_from_pos(symbol, timeframe, start_pos, count)  # Solicita os dados ao MetaTrader