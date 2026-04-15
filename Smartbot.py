import os
import requests
import time
import json
import re
from google import genai
from google.genai import types

# --- НАСТРОЙКИ ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8720043003:AAFAdFvep5cKT02mzu2VG71USVwsJFrJYVc")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyDqt_jrbpsNYQq4ZOiJLO47HcaFwepk8Ms")

# Инициализация Gemini
client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_ID = "gemini-1.5-flash"

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={
            "chat_id": chat_id, 
            "text": text, 
            "parse_mode": "Markdown"
        }, timeout=30)
    except Exception as e:
        print(f"Ошибка отправки: {e}")

def get_file_path(file_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_id}"
    r = requests.get(url).json()
    return r['result']['file_path']

def download_file(file_path):
    # Исправленный URL скачивания
    url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
    r = requests.get(url)
    return r.content

def analyze_all(item_text=None, image_bytes=None):
    """
    Анализ товара через Gemini 1.5 Flash
    """
    prompt = """Ты — эксперт по продажам на Avito. 
    Проанализируй товар. Напиши ОДНО идеальное продающее описание (3-4 предложения).
    Верни ответ СТРОГО в формате JSON на русском языке:
    {
        "name": "точное название товара",
        "description": "текст описания",
        "min_price": число,
        "max_price": число,
        "avg_price": число,
        "trend": "растёт/падает/стабилен",
        "advice": "короткий совет по продаже"
    }"""

    try:
        content = [prompt]
        if item_text:
            content.append(f"Контекст от пользователя: {item_text}")
        if image_bytes:
            content.append(types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg'))

        # Запрос к AI
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=content
        )
        
        # Извлекаем JSON из ответа (убираем возможный лишний текст)
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return None
    except Exception as e:
        print(f"Ошибка анализа: {e}")
        return None

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    try:
        r = requests.get(url, params={"timeout": 30, "offset": offset}, timeout=35)
        return r.json().get('result', [])
    except:
        return []

print("🚀 SmartSell Pro запущен и готов к работе!")

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
                send_message(chat_id, "🤖 Привет! Я помогу оценить товар для Avito.\n\nПришли мне **название товара** или **фото**, и я проанализирую рынок!")
                continue

            item_data = None
            
            if photo:
                send_message(chat_id, "📸 Вижу фото, анализирую...")
                file_id = photo[-1]['file_id']
                file_path = get_file_path(file_id)
                image_bytes = download_file(file_path)
                item_data = analyze_all(item_text=caption, image_bytes=image_bytes)
            elif text:
                send_message(chat_id, "📊 Ищу информацию по названию...")
                item_data = analyze_all(item_text=text)

            if item_data:
                res = (
                    f"📦 *Товар:* {item_data.get('name')}\n\n"
                    f"📝 *Описание:* {item_data.get('description')}\n\n"
                    f"💰 *Цены:*\n"
                    f"• Средняя: {item_data.get('avg_price')}₽\n"
                    f"• Диапазон: {item_data.get('min_price')} - {item_data.get('max_price')}₽\n\n"
                    f"📈 *Тренд:* {item_data.get('trend')}\n"
                    f"💡 *Совет:* {item_data.get('advice')}"
                )
                send_message(chat_id, res)
            else:
                if text != '/start':
                    send_message(chat_id, "❌ Не удалось распознать товар. Попробуй еще раз или напиши название текстом.")

    except Exception as e:
        print(f"Ошибка в цикле: {e}")
        time.sleep(5)
