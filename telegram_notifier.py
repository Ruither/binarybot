# Contém a função responsável por enviar mensagens formatadas ao Telegram

import requests
# Envia uma mensagem de texto para um chat do Telegram usando o token do bot
# :param bot_token: Token do bot fornecido pelo BotFather
# :param chat_id: ID do chat (grupo ou privado) onde a mensagem será enviada
# :param message: Texto formatado da mensagem (em HTML)
def send_telegram_message(bot_token, chat_id, message):
    # Monta a URL da API de envio de mensagem do Telegram
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    # Cria o payload com os dados da mensagem
    payload = {
        "chat_id": chat_id,         # ID do destino da mensagem
        "text": message,           # Conteúdo da mensagem
        "parse_mode": "HTML"      # Formatação do conteúdo (HTML permite tags como <b>, <code>, etc)
    }
    try:
        # Envia a requisição POST para a API do Telegram
        response = requests.post(url, data=payload)
        # Se o status da resposta não for 200 (OK), imprime erro
        if response.status_code != 200:
            print(f"Falha ao enviar mensagem: {response.text}")
    except Exception as e:
        # Captura e imprime qualquer exceção durante a tentativa de envio
        print(f"Erro ao enviar mensagem para o Telegram: {e}")