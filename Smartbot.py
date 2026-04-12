import os
import requests
import time
import json
import re

TELEGRAM_TOKEN = os.environ.get('8720043003:AAHgZKlAMo6T63maN-oFLa4EvqTwgxiiS4g')
DEEPSEEK_API_KEY = os.environ.get('sk-92d2a007832043e5a482856694a2be73')

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=30)
    except Exception as e:
        print(f"Ошибка: {e}")

def get_deepseek(prompt):
    response = requests.post(
        "https://api.deepseek.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
        json={
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 800,
            "temperature": 0.5
        },
        timeout=60
    )
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    return f"Ошибка API: {response.status_code}"

def analyze_market(item_name):
    prompt = f"""Ты — аналитик рынка Avito. Проанализируй товар: "{item_name}"
Ответь ТОЛЬКО JSON: {{"min_price": число, "max_price": число, "recommended_price": число, "advice": "совет"}}"""
    try:
        response = get_deepseek(prompt)
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            return json.loads(match.group())
        return None
    except:
        return None

def get_description(item_name):
    prompt = f"""Напиши ОДНО продающее описание для Avito товара: {item_name}
Стиль: деловой, серьёзный. 3-4 предложения. Без сленга. Без фраз "торг уместен". Только текст описания."""
    return get_deepseek(prompt)

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    try:
        r = requests.get(url, params={"timeout": 30, "offset": offset}, timeout=35)
        return r.json().get('result', [])
    except:
        return []

def main():
    print("✅ SmartSell Pro запущен!")
    last_id = None
    while True:
        try:
            for update in get_updates(last_id):
                last_id = update['update_id'] + 1
                msg = update.get('message')
                if not msg:
                    continue
                chat_id = msg['chat']['id']
                text = msg.get('text', '')
                if text == '/start':
                    send_message(chat_id, "Отправьте описание товара — я сделаю анализ и продающее описание")
                    continue
                if text:
                    send_message(chat_id, "📊 Анализирую...")
                    market = analyze_market(text)
                    if market:
                        send_message(chat_id, f"💰 Рек. цена: {market.get('recommended_price', '?')} руб.\n💡 {market.get('advice', '')}")
                    desc = get_description(text)
                    send_message(chat_id, f"📝 Описание:\n{desc}")
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()