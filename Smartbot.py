import requests
import time
import json
import re
import base64

# --- НАСТРОЙКИ ---
TELEGRAM_TOKEN = "8720043003:AAFAdFvep5cKT02mzu2VG71USVwsJFrJYVc"
YANDEX_API_KEY = "AQVN07AhchaQwE8BSAmMcjwEwM2EgBnCtZ5E9Szt"
FOLDER_ID = "b1gncknlc4lj0a8rlnla"

# 1. Функция OCR: извлекает ТЕКСТ из картинки
def extract_text_from_image(image_bytes):
    url = "https://vision.api.cloud.yandex.net/vision/v1/batchAnalyze"
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    
    payload = {
        "analyzeSpecs": [{
            "content": base64_image,
            "features": [{
                "type": "TEXT_DETECTION",
                "textDetectionConfig": {
                    "languageCodes": ["ru", "en"],
                    "model": "page"
                }
            }]
        }]
    }
    headers = {"Authorization": f"Api-Key {YANDEX_API_KEY}", "Content-Type": "application/json"}
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=15).json()
        blocks = res['results'][0]['results'][0].get('textAnnotation', {}).get('blocks', [])
        full_text = ""
        for block in blocks:
            for line in block['lines']:
                full_text += line['text'] + " "
        return full_text.strip()
    except Exception as e:
        print(f"Ошибка OCR: {e}")
        return ""

# 2. Функция GPT: оценивает товар на основе текста
def ask_yandex_gpt(query_text):
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {"Authorization": f"Api-Key {YANDEX_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt/latest",
        "completionOptions": {"stream": False, "temperature": 0.3, "maxTokens": "1000"},
        "messages": [
            {"role": "system", "text": "Ты эксперт Avito. Твоя задача: проанализировать текст (возможно из OCR) и оценить товар. Верни СТРОГО JSON: {\"name\": \"название\", \"description\": \"краткое описание\", \"avg_price\": \"цена\", \"advice\": \"совет\"}"},
            {"role": "user", "text": f"Проанализируй данные о товаре: {query_text}"}
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        text_res = response.json()['result']['alternatives'][0]['message']['text']
        match = re.search(r'\{.*\}', text_res, re.DOTALL)
        return json.loads(match.group()) if match else None
    except: return None

def send_tg(chat_id, text):
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                  json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})

last_id = 0
print("🚀 SmartSell Pro с поддержкой OCR запущен!")

while True:
    try:
        updates = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates", params={"offset": last_id + 1, "timeout": 30}).json().get('result', [])
        for update in updates:
            last_id = update['update_id']
            msg = update.get('message')
            if not msg: continue
            chat_id = msg['chat']['id']

            # Если прислали ФОТО
            if msg.get('photo'):
                send_tg(chat_id, "🔍 Считываю текст с фото...")
                file_id = msg['photo'][-1]['file_id']
                f_info = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_id}").json()
                img_data = requests.get(f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{f_info['result']['file_path']}").content
                
                # Шаг 1: OCR
                ocr_text = extract_text_from_image(img_data)
                user_caption = msg.get('caption', '')
                full_info = f"{ocr_text} {user_caption}".strip()
                
                if not full_info:
                    send_tg(chat_id, "Не удалось ничего прочитать на фото. Попробуй сделать фото четче или добавь описание текстом.")
                    continue
                
                send_tg(chat_id, f"📝 Прочитано: _{ocr_text[:50]}..._ \n📊 Оцениваю цену...")
                
                # Шаг 2: GPT
                data = ask_yandex_gpt(full_info)

            # Если прислали ТЕКСТ
            elif msg.get('text'):
                if msg['text'] == '/start':
                    send_tg(chat_id, "Привет! Скинь фото товара или его название, и я скажу рыночную цену.")
                    continue
                send_tg(chat_id, "📊 Анализирую...")
                data = ask_yandex_gpt(msg['text'])

            if data:
                res = f"📦 *{data.get('name')}*\n\n{data.get('description')}\n\n💰 *Цена:* {data.get('avg_price')}\n💡 *Совет:* {data.get('advice')}"
                send_tg(chat_id, res)
                
    except Exception as e:
        print(f"Ошибка: {e}")
        time.sleep(3)
