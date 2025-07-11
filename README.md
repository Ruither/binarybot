Este projeto é um robô de análise técnica automatizada para **opções binárias**, focado em **gráficos M5**, com lógica baseada em **suporte/resistência, padrões de velas, retrações, lateralização, e filtros por notícias de alto impacto**. Ele coleta dados do **MetaTrader 5**, analisa condições de entrada e envia **sinais de compra ou venda via Telegram**.

---

## ✅ Funcionalidades

- 📈 Coleta automática de candles M1/M5/M15/M30/H1 via MetaTrader5
- 🔍 Cálculo de **suporte e resistência** com múltiplos toques, distância mínima e tolerância por pips
- 📉 Verificação de **lateralização do mercado**
- 🕯️ Reconhecimento de **retração**, **velas esticadas** e **pavio em direção da operação**
- 📰 Bloqueio automático de sinais baseado em **notícias de alto impacto (Investing.com - USD/EUR)**
- 📬 Envio de sinais com resultado final para grupo do **Telegram**
- ⏱️ Totalmente automatizado e com controle de **janela de operação por horário**

---

## 🧠 Regras e Validações Técnicas

### 1. **Suporte e Resistência**
- Calculado com base nas últimas **72 velas (M5)**, ignorando as **6 mais recentes**
- **Mínimo de 2 toques** exigido na mesma faixa de preço
- **Distância mínima de velas entre os toques**: `5 velas`
- **Tolerância por pips**: `2` pips (ajustável)
- Clusters são agrupados por aproximação de preço (binning)

### 2. **Lateralização**
- Detectada por faixa de variação nas últimas 36 velas
- Evita operar em tendências fortes

### 3. **Condições da Vela Atual**
- Verifica **retração mínima** de corpo vs pavio (ex: pavio ≥ 20%)
- Avalia se a vela está **esticada** (corpo dominante ≥ 70% do candle total)

### 4. **Validação de Pavio nas Velas Anteriores**
- Duas últimas velas devem apresentar **pavio consistente com a direção**
- Regras:
  - Para `buy`: pavio inferior ≥ 20% do corpo e pavio superior ≤ 40%
  - Para `sell`: pavio superior ≥ 20% do corpo e pavio inferior ≤ 40%

### 5. **Filtro por Notícias Econômicas**
- Notícias com **3 estrelas** e moedas `USD` ou `EUR`
- Bloqueia sinais **15 minutos antes e 15 minutos depois** do evento
- Fonte: **Investing.com (versão brasileira)**

---

## 🚀 Sinal Enviado para o Telegram

Exemplo de mensagem enviada:

```
<b>NEW Time:</b> <code>10:01:27 🕐</code>
<b>Symbol:</b> <code>GBPJPY 📊</code>
<b>Signal:</b> <code>sell ⬇️</code>
<b>Price:</b> <code>198.380 💰</code>
```

E após o fechamento da vela:

```
<b>NEW Symbol:</b> <code>GBPJPY 📊</code>
<b>Price:</b> <code>198.310 💰</code>
<b>Resultado:</b> <code>NEW Successful ✅</code>

<b>Histórico:</b>
<b>Total:</b> <code>12</code>
<b>Successful:</b> <code>9 ✅</code>
<b>Failure:</b> <code>3 ❌</code>
```

---

## ⚙️ Estrutura dos Arquivos

| Arquivo | Função |
|--------|--------|
| `main.py` | Orquestra o funcionamento do robô (loop, horários, execução geral) |
| `support_resistance.py` | Cálculo de suporte/resistência com lógica de toques e clusters |
| `patterns.py` | Validação de retração, esticamento e pavios das velas |
| `lateralization.py` | Verifica se o mercado está lateral |
| `signals.py` | Avalia possíveis entradas e checa se o sinal foi bem-sucedido |
| `investing_news.py` | Faz scraping de notícias econômicas e aplica bloqueio de sinais |
| `telegram_notifier.py` | Envia mensagens para Telegram via Bot API |
| `mt5_collector.py` | Interface com MetaTrader 5 para coletar dados históricos |
| `config.yaml` | Arquivo de configuração com pares, horários, Telegram, parâmetros técnicos |

---
