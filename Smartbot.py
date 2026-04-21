import os
import requests
import time
import json
import re
import base64

# --- ПОЛУЧЕНИЕ НАСТРОЕК ---
TOKEN = os.getenv("8720043003:AAFAdFvep5cKT02mzu2VG71USVwsJFrJYVc")
API_KEY = os.getenv("AQVN2rb8ui_yOuciZ-FUFWHg-DnYqUCCrScke9Jh")
FOLDER_ID = os.getenv("b1gb3ata3o666f6rk33a")

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=30)
    except Exception as e:
        print(f"Ошибка отправки: {e}")

def get_file_path(file_id):
    url = f"https://api.telegram.org/bot{TOKEN}/getFile?file_id={file_id}"
    return requests.get(url).json()['result']['file_path']

def download_file(file_path):
    url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
    return requests.get(url).content

# --- ФУНКЦИЯ АНАЛИЗА (Vision + GPT) ---

def analyze_avito(item_text=None, image_bytes=None):
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {API_KEY}"
    }

    # Формируем контент запроса
    prompt = "Ты — эксперт Авито. Оцени товар на фото или по описанию. Напиши продающее описание и цены. Ответь ТОЛЬКО в формате JSON: {'item_name': '...', 'description': '...', 'price_min': 0, 'price_max': 0, 'price_avg': 0, 'trend': '...', 'advice': '...'}"
    if item_text:
        prompt += f" Контекст: {item_text}"

    # Собираем мультимодальное сообщение
    user_content = [{"type": "text", "text": prompt}]
    
    if image_bytes:
        encoded_image = base64.b64encode(image_bytes).decode('utf-8')
        user_content.append({
            "type": "image",
            "image": {
                "content": encoded_image
            }
        })

    payload = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt/latest",
        "completionOptions": {"temperature": 0.5, "maxTokens": 1500},
        "messages": [
            {
                "role": "user",
                "content": user_content
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=40)
        res_data = response.json()
        
        if 'result' not in res_data:
            print(f"Ошибка API: {res_data}")
            return None

        raw_text = res_data['result']['alternatives'][0]['message']['text']
        
        # Поиск JSON в тексте
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return None
    except Exception as e:
        print(f"Ошибка в analyze_avito: {e}")
        return None

# --- ОСНОВНОЙ ЦИКЛ ---

offset = 0
print("💰 SmartSell Pro (Yandex Vision) запущен!")

while True:
    try:
        updates_url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
        r = requests.get(updates_url, params={"offset": offset, "timeout": 30}).json()
        
        for update in r.get("result", []):
            offset = update["update_id"] + 1
            msg = update.get("message")
            if not msg: continue
            
            chat_id = msg["chat"]["id"]
            text = msg.get("text")
            photo = msg.get("photo")
            caption = msg.get("caption")

            if text == "/start":
                send_message(chat_id, "🤝 Привет! Пришли фото товара или название, и я сделаю описание для Авито.")
                continue

            item_data = None
            if photo:
                send_message(chat_id, "📸 Изучаю фото товара через Yandex Vision...")
                file_path = get_file_path(photo[-1]['file_id'])
                img_bytes = download_file(file_path)
                item_data = analyze_avito(item_text=caption, image_bytes=img_bytes)
            elif text:
                send_message(chat_id, "📊 Анализирую рынок по названию...")
                item_data = analyze_avito(item_text=text)

            if item_data:
                res = (
                    f"📦 *Товар:* {item_data.get('item_name')}\n\n"
                    f"📝 *Описание:*\n{item_data.get('description')}\n\n"
                    f"💰 *Цены:* {item_data.get('price_min')} - {item_data.get('price_max')}₽\n"
                    f"📈 *Тренд:* {item_data.get('trend')}\n"
                    f"💡 *Совет:* {item_data.get('advice')}"
                )
                send_message(chat_id, res)
            else:
                if text != "/start":
                    send_message(chat_id, "⚠️ Не удалось распознать товар. Попробуй еще раз.")
                    
    except Exception as e:
        print(f"Ошибка: {e}")
        time.sleep(3)
