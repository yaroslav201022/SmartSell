import os
import requests
import time
import json
import re
import google.generativeai as genai

# Настройки (Рекомендуется использовать переменные окружения)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8720043003:AAFAdFvep5cKT02mzu2VG71USVwsJFrJYVc")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AlzaSyBsunXzA9PrgGiFzfVrdJjwOHdn-DYwaqro")

genai.configure(api_key=GEMINI_API_KEY)
# Используем системную инструкцию для более стабильного JSON
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    generation_config={"response_mime_type": "application/json"}
)

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}, timeout=30)
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")

def get_file_path(file_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_id}"
    r = requests.get(url).json()
    return r['result']['file_path']

def download_file(file_path):
    url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
    r = requests.get(url)
    return r.content

def analyze_all(item_text=None, image_bytes=None):
    prompt = f"""Ты — эксперт по продажам на Avito. 
    Проанализируй товар {f'из описания: "{item_text}"' if item_text else 'по предоставленному фото'}.
    
    1. Определи, что это за товар.
    2. Напиши ОДНО идеальное продающее описание (3-4 предложения, без клише).
    3. Проведи анализ рынка.
    
    Верни ответ СТРОГО в формате JSON:
    {{
        "name": "точное название товара",
        "description": "текст описания",
        "min_price": число,
        "max_price": число,
        "avg_price": число,
        "trend": "растёт/падает/стабилен",
        "advice": "короткий совет по продаже"
    }}"""

    try:
        content = [prompt]
        if image_bytes:
            content.append({'mime_type': 'image/jpeg', 'data': image_bytes})
        
        response = model.generate_content(content)
        
        # Парсим JSON (с учетом того, что Gemini 1.5 Flash хорошо держит формат)
        return json.loads(response.text)
    except Exception as e:
        print(f"Ошибка анализа Gemini: {e}")
        return None

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    try:
        r = requests.get(url, params={"timeout": 30, "offset": offset}, timeout=35)
        return r.json().get('result', [])
    except Exception as e:
        print(f"Ошибка получения обновлений: {e}")
        return []

print("🚀 SmartSell Pro запущен!")

last_id = None
while True:
    try:
        updates = get_updates(last_id)
        for update in updates:
            last_id = update['update_id'] + 1
            msg = update.get('message')
            if not msg: continue
            
            chat_id = msg['chat']['id']
            photo = msg.get('photo')
            text = msg.get('text')
            caption = msg.get('caption')

            if text == '/start':
                send_message(chat_id, "👋 Привет! Пришлите фото товара или его название — я составлю описание и оценю цену.")
                continue

            item_data = None
            if photo:
                send_message(chat_id, "📸 Изучаю фото...")
                file_id = photo[-1]['file_id']
                file_path = get_file_path(file_id)
                image_bytes = download_file(file_path)
                item_data = analyze_all(item_text=caption, image_bytes=image_bytes)
            elif text:
                send_message(chat_id, "📊 Анализирую текст...")
                item_data = analyze_all(item_text=text)

            if item_data:
                res = (f"📦 *Товар:* {item_data.get('name')}\n\n"
                       f"📝 *Описание:* {item_data.get('description')}\n\n"
                       f"💰 *Цены:*\n"
                       f"• Средняя: {item_data.get('avg_price')}₽\n"
                       f"• Диапазон: {item_data.get('min_price')} - {item_data.get('max_price')}₽\n\n"
                       f"📈 *Тренд:* {item_data.get('trend')}\n"
                       f"💡 *Совет:* {item_data.get('advice')}")
                send_message(chat_id, res)
            elif not text == '/start':
                send_message(chat_id, "❌ Не удалось проанализировать товар. Попробуйте другое фото или текст.")

    except Exception as e:
        print(f"Критическая ошибка цикла: {e}")
        time.sleep(5)
