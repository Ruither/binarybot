# === investing_news.py ===
# Alternativa: busca eventos econômicos usando API AJAX do Investing.com (versão brasileira)

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

def buscar_noticias_importantes():
    """
    Faz scraping da API de backend do Investing.com (versão brasileira)
    para obter eventos do dia atual para moedas relevantes (USD, EUR, JPY, CHF, AUD, NZD),
    incluindo o nível de impacto (1 a 3 estrelas).
    """
    url = "https://br.investing.com/economic-calendar/Service/getCalendarFilteredData"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://br.investing.com",
        "Referer": "https://br.investing.com/economic-calendar/"
    }

    hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    payload = {
        "timeFilter": "timeOnly",
        "dateFrom": hoje,
        "dateTo": hoje,
        "currentTab": "custom"
    }

    response = requests.post(url, headers=headers, data=payload)
    if response.status_code != 200:
        return []

    html_data = response.json().get("data", "")
    if not html_data.strip():
        return []

    soup = BeautifulSoup(html_data, "html.parser")

    eventos = []
    moedas_relevantes = {"USD", "EUR"}

    linhas = soup.select("tr.js-event-item")
    for linha in linhas:
        try:
            hora_elem = linha.select_one("td.first.left.time")
            moeda_elem = linha.select_one("td.left.flagCur.noWrap")
            desc_elem = linha.select_one("td.left.event")
            impacto_container = linha.select_one("td.sentiment")

            if not hora_elem or not moeda_elem or not desc_elem or not impacto_container:
                continue

            hora_str = hora_elem.text.strip()
            moeda = moeda_elem.text.strip()
            descricao = desc_elem.text.strip()

            if moeda not in moedas_relevantes:
                continue

            # Define o impacto com base no atributo 'data-img_key'
            estrelas = 0
            data_img = impacto_container.get("data-img_key", "").lower()
            if "bull1" in data_img:
                estrelas = 1
            elif "bull2" in data_img:
                estrelas = 2
            elif "bull3" in data_img:
                estrelas = 3

            if estrelas < 3:
                continue  # ignora eventos com menos de 3 estrelas

            try:
                hora_evento = datetime.strptime(hora_str, "%H:%M").replace(
                    year=datetime.now(timezone.utc).year,
                    month=datetime.now(timezone.utc).month,
                    day=datetime.now(timezone.utc).day
                ) #- timedelta(hours=1)  # diminui 1 hora para alinhar com o horário exibido no site
            except ValueError:
                continue

            eventos.append({
                "moeda": moeda,
                "horario": hora_evento,
                "descricao": descricao,
                "impacto": estrelas
            })

        except Exception:
            continue

    return eventos

def dentro_de_janela_de_noticia(horario_atual, eventos, margem_minutos=15):
    for evento in eventos:
        janela_inicio = evento['horario'] - timedelta(minutes=margem_minutos)
        janela_fim = evento['horario'] + timedelta(minutes=margem_minutos)
        if janela_inicio <= horario_atual <= janela_fim:
            return True
    return False

if __name__ == "__main__":
    eventos = buscar_noticias_importantes()
    for evento in eventos:
        print(f"{evento['horario'].strftime('%H:%M')} - {evento['moeda']} - {evento['descricao']} ({evento['impacto']})")

    agora = datetime.now()
    if dentro_de_janela_de_noticia(agora, eventos):
        print("Sinais bloqueados por notícia relevante!")
    else:
        print("Permissão para gerar sinais.")
