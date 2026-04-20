import os
import requests
import time
import json
import re
import base64

# --- НАСТРОЙКИ ---
TELEGRAM_TOKEN = "8720043003:AAFAdFvep5cKT02mzu2VG71USVwsJFrJYVc"
YANDEX_API_KEY = "AQVNwTN0DIGQEXuBQZc3lyx_FZJ5G22pp1WSQw-C"
FOLDER_ID = "b1gncknlc4lj0a8rlnla"

# --- ФУНКЦИИ ТЕЛЕГРАМА ---

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=30)
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")

def get_file_path(file_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_id}"
    return requests.get(url).json()['result']['file_path']

def download_file(file_path):
    url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
    return requests.get(url).content

# --- ФУНКЦИЯ YANDEX GPT ---

def analyze_avito(item_text=None, image_bytes=None):
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    
    # Промпт, заточенный под Авито
    system_prompt = """Ты — профессиональный аналитик маркетплейса Avito.
    Твоя задача: составить продающее описание и оценить цену товара.
    Ответь СТРОГО в формате JSON (без лишнего текста):
    {
        "item_name": "название товара",
        "description": "продающее описание (3-4 предложения)",
        "price_min": число,
        "price_max": число,
        "price_avg": число,
        "trend": "растёт/стабилен/падает",
        "advice": "короткий совет по быстрой продаже"
    }"""
    
    user_input = f"Товар: {item_text}" if item_text else "Проанализируй товар на фото."
    
    messages = [
        {"role": "system", "text": system_prompt},
        {"role": "user", "text": user_input}
    ]

    # Примечание: Для полноценного Vision (анализа фото) в Яндексе используется модель 'yandexgpt-with-vision'
    # Если она еще не активна в твоем тарифе, используй 'yandexgpt/latest' для текста
    payload = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt/latest",
        "completionOptions": {"temperature": 0.5, "maxTokens": 1500},
        "messages": messages
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {YANDEX_API_KEY}"
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        res_data = response.json()
        raw_text = res_data['result']['alternatives'][0]['message']['text']
        
        # Очистка JSON
        clean_json = re.search(r'\{.*\}', raw_text, re.DOTALL).group()
        return json.loads(clean_json)
    except Exception as e:
        print(f"Ошибка Yandex API: {e}")
        return None

# --- ОСНОВНОЙ ЦИКЛ ---

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    try:
        r = requests.get(url, params={"timeout": 30, "offset": offset}, timeout=35)
        return r.json().get('result', [])
    except: return []

print("💰 SmartSell Pro (Yandex) запущен и готов к торгам!")

last_id = None
while True:
    try:
        for update in get_updates(last_id):
            last_id = update['update_id'] + 1
            msg = update.get('message')
            if not msg: continue
            
            chat_id = msg['chat']['id']
            photo = msg.get('photo')
            text = msg.get('text')
            caption = msg.get('caption')

            if text == '/start':
                send_message(chat_id, "🤝 Привет! Пришли название товара или фото, и я подготовлю всё для продажи на Avito.")
                continue

            item_data = None
            if photo:
                send_message(chat_id, "📸 Изучаю фото товара...")
                file_path = get_file_path(photo[-1]['file_id'])
                img_bytes = download_file(file_path)
                item_data = analyze_avito(item_text=caption, image_bytes=img_bytes)
            elif text:
                send_message(chat_id, "📊 Анализирую рынок...")
                item_data = analyze_avito(item_text=text)

            if item_data:
                res = f"""📦 *Товар:* {item_data.get('item_name')}

📝 *Описание для Avito:*
{item_data.get('description')}

💰 *Анализ цен:*
• Средняя: {item_data.get('price_avg')}₽
• Диапазон: {item_data.get('price_min')} - {item_data.get('price_max')}₽

📈 *Тренд:* {item_data.get('trend')}
💡 *Совет:* {item_data.get('advice')}"""
                send_message(chat_id, res)
            else:
                if text != '/start':
                    send_message(chat_id, "⚠️ Ошибка анализа. Попробуй еще раз или напиши название текстом.")

    except Exception as e:
        print(f"Ошибка цикла: {e}")
        time.sleep(5)
