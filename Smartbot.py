import requests
import time
import json
import re
import base64

# --- НАСТРОЙКИ (ЗАПОЛНИ ЭТИ ДАННЫЕ) ---
TELEGRAM_TOKEN = "8720043003:AAFAdFvep5cKT02mzu2VG71USVwsJFrJYVc"
YANDEX_API_KEY = "AQVN07AhchaQwE8BSAmMcjwEwM2EgBnCtZ5E9Szt"
FOLDER_ID = "b1gncknlc4lj0a8rlnla"

def extract_info_from_image(image_bytes):
    """Шаг 1: Используем Yandex Vision (OCR + Объекты)"""
    url = "https://vision.api.cloud.yandex.net/vision/v1/batchAnalyze"
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    
    payload = {
        "analyzeSpecs": [{
            "content": base64_image,
            "features": [
                {"type": "TEXT_DETECTION", "textDetectionConfig": {"languageCodes": ["ru", "en"]}},
                {"type": "CLASSIFICATION"}
            ]
        }]
    }
    headers = {"Authorization": f"Api-Key {YANDEX_API_KEY}", "Content-Type": "application/json"}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        res_data = response.json()
        result = res_data['results'][0]['results'][0]
        
        # Собираем текст, если он есть
        ocr_text = ""
        blocks = result.get('textAnnotation', {}).get('blocks', [])
        for block in blocks:
            for line in block['lines']:
                ocr_text += line['text'] + " "
        
        # Если текста мало/нет, берем название объекта
        labels = result.get('classification', {}).get('predictions', [])
        object_name = labels[0]['label'] if labels else ""
        
        return f"{object_name} {ocr_text}".strip()
    except Exception as e:
        print(f"Ошибка Vision: {e}")
        return ""

def ask_yandex_gpt(query_text):
    """Шаг 2: Используем YandexGPT для оценки"""
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {"Authorization": f"Api-Key {YANDEX_API_KEY}", "Content-Type": "application/json"}
    
    payload = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt/latest",
        "completionOptions": {"stream": False, "temperature": 0.3, "maxTokens": "1000"},
        "messages": [
            {
                "role": "system", 
                "text": "Ты эксперт Avito. Оцени товар по описанию. Верни СТРОГО JSON: {\"name\": \"название\", \"description\": \"краткое описание\", \"avg_price\": \"цена\", \"advice\": \"совет\"}"
            },
            {"role": "user", "text": f"Проанализируй товар: {query_text}"}
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        full_res = response.json()['result']['alternatives'][0]['message']['text']
        match = re.search(r'\{.*\}', full_res, re.DOTALL)
        return json.loads(match.group()) if match else None
    except Exception as e:
        print(f"Ошибка GPT: {e}")
        return None

def send_tg(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})

def main():
    last_id = 0
    print("🚀 SmartSell Pro (OCR + Vision) успешно запущен!")
    
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
            res = requests.get(url, params={"offset": last_id + 1, "timeout": 30}).json()
            
            for update in res.get('result', []):
                last_id = update['update_id']
                msg = update.get('message')
                if not msg: continue
                chat_id = msg['chat']['id']

                # Если прислали ФОТО
                if msg.get('photo'):
                    send_tg(chat_id, "🔍 Анализирую фото и текст...")
                    file_id = msg['photo'][-1]['file_id']
                    f_info = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_id}").json()
                    img_data = requests.get(f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{f_info['result']['file_path']}").content
                    
                    # Получаем информацию из фото
                    detected_info = extract_info_from_image(img_data)
                    caption = msg.get('caption', '')
                    final_query = f"{detected_info} {caption}".strip()
                    
                    if not final_query:
                        send_tg(chat_id, "❌ Не удалось распознать товар. Попробуй описать его текстом.")
                        continue
                    
                    data = ask_yandex_gpt(final_query)

                # Если прислали ТЕКСТ
                elif msg.get('text'):
                    text_input = msg['text']
                    if text_input == '/start':
                        send_tg(chat_id, "Привет! Пришли фото товара (желательно с текстом/коробкой) или просто напиши название.")
                        continue
                    send_tg(chat_id, "📊 Оцениваю...")
                    data = ask_yandex_gpt(text_input)

                # Вывод результата
                if data:
                    res_msg = (
                        f"📦 *{data.get('name', 'Товар')}*\n\n"
                        f"{data.get('description', '')}\n\n"
                        f"💰 *Цена:* {data.get('avg_price', 'Не определена')}\n"
                        f"💡 *Совет:* {data.get('advice', '-')}"
                    )
                    send_tg(chat_id, res_msg)
                else:
                    send_tg(chat_id, "⚠️ Ошибка при анализе. Попробуй уточнить запрос.")

        except Exception as e:
            print(f"Сбой цикла: {e}")
            time.sleep(3)

if __name__ == "__main__":
    main()
