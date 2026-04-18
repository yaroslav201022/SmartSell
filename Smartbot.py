import os, requests, time, json, re
from google import genai
from google.genai import types

# --- НАСТРОЙКИ (ОБЯЗАТЕЛЬНО ЗАПОЛНИ) ---
TELEGRAM_TOKEN = "8720043003:AAFAdFvep5cKT02mzu2VG71USVwsJFrJYVc"
GEMINI_API_KEY = "AIzaSyDqt_jrbpsNYQq4ZOiJLO47HcaFwepk8Ms" 

client = genai.Client(api_key=GEMINI_API_KEY)

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def analyze_all(item_text=None, image_bytes=None):
    prompt = "Ты эксперт Avito. Проанализируй товар. Напиши краткое описание. Верни СТРОГО JSON: {\"name\": \"название\", \"description\": \"текст\", \"avg_price\": \"цена\", \"advice\": \"совет\"}"
    try:
        content = [prompt]
        if item_text: content.append(f"Запрос: {item_text}")
        if image_bytes: content.append(types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg'))
        
        response = client.models.generate_content(model="gemini-1.5-flash", contents=content)
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        return json.loads(match.group()) if match else None
    except Exception as e:
        print(f"Ошибка AI: {e}")
        return None

last_id = None
print("🚀 Бот запущен!")

while True:
    try:
        res = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates", params={"offset": last_id, "timeout": 20}).json()
        for update in res.get('result', []):
            last_id = update['update_id'] + 1
            msg = update.get('message')
            if not msg: continue
            chat_id = msg['chat']['id']
            
            if msg.get('text') == '/start':
                send_message(chat_id, "Привет! Пришли название товара или фото.")
                continue

            if msg.get('photo'):
                send_message(chat_id, "📸 Изучаю фото...")
                file_info = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={msg['photo'][-1]['file_id']}").json()
                img_data = requests.get(f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_info['result']['file_path']}").content
                data = analyze_all(item_text=msg.get('caption'), image_bytes=img_data)
            elif msg.get('text'):
                send_message(chat_id, "📊 Анализирую...")
                data = analyze_all(item_text=msg.get('text'))

            if data:
                res_text = f"📦 *{data.get('name')}*\n\n{data.get('description')}\n\n💰 *Цена:* {data.get('avg_price')}\n💡 *Совет:* {data.get('advice')}"
                send_message(chat_id, res_text)
            else:
                send_message(chat_id, "❌ Не удалось распознать. Попробуй еще раз.")
    except Exception as e:
        print(f"Ошибка: {e}")
        time.sleep(2)
