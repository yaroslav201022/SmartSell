import requests
import time
import json
import re

# --- ТВОИ ДАННЫЕ (ВСТАВЬ СЮДА) ---
TELEGRAM_TOKEN = "8720043003:AAFAdFvep5cKT02mzu2VG71USVwsJFrJYVc"
YANDEX_API_KEY = "AQVN07AhchaQwE8BSAmMcjwEwM2EgBnCtZ5E9Szt"
FOLDER_ID = "b1gncknlc4lj0a8rlnla"

def ask_yandex(query):
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Authorization": f"Api-Key {YANDEX_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt/latest",
        "completionOptions": {"stream": False, "temperature": 0.5, "maxTokens": "1000"},
        "messages": [
            {"role": "system", "text": "Ты эксперт Avito. Проанализируй товар. Верни СТРОГО JSON: {\"name\": \"название\", \"description\": \"текст\", \"avg_price\": \"цена\", \"advice\": \"совет\"}"},
            {"role": "user", "text": query}
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        text_res = response.json()['result']['alternatives'][0]['message']['text']
        match = re.search(r'\{.*\}', text_res, re.DOTALL)
        return json.loads(match.group()) if match else None
    except Exception as e:
        print(f"Ошибка Яндекса: {e}")
        return None

def send_tg(chat_id, text):
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                  json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})

last_id = 0
print("🚀 Бот на YandexGPT запущен!")

while True:
    try:
        res = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates", params={"offset": last_id + 1, "timeout": 30}).json()
        for update in res.get('result', []):
            last_id = update['update_id']
            if 'message' not in update or 'text' not in update['message']: continue
            
            chat_id = update['message']['chat']['id']
            user_text = update['message']['text']
            
            if user_text == "/start":
                send_tg(chat_id, "Привет! Я эксперт Avito. Напиши, какой товар оценить?")
                continue

            send_tg(chat_id, "📡 Запрос отправлен в Яндекс...")
            data = ask_yandex(user_text)

            if data:
                output = f"📦 *{data.get('name')}*\n\n{data.get('description')}\n\n💰 *Цена:* {data.get('avg_price')}\n💡 *Совет:* {data.get('advice')}"
                send_tg(chat_id, output)
            else:
                send_tg(chat_id, "❌ Яндекс не смог обработать этот товар. Попробуй другое название.")
    except Exception as e:
        print(f"Ошибка связи: {e}")
        time.sleep(3)
