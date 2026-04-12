import os
import requests
import time

TELEGRAM_TOKEN = os.environ.get('8720043003:AAHgZKlAMo6T63maN-oFLa4EvqTwgxiiS4g')

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=30)
    except Exception as e:
        print(f"Ошибка: {e}")

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    try:
        r = requests.get(url, params={"timeout": 30, "offset": offset}, timeout=35)
        return r.json().get('result', [])
    except:
        return []

print("✅ Бот запущен!")

last_id = None
while True:
    try:
        for update in get_updates(last_id):
            last_id = update['update_id'] + 1
            msg = update.get('message')
            if msg and msg.get('text'):
                chat_id = msg['chat']['id']
                text = msg['text']
                if text == '/start':
                    send_message(chat_id, "👋 Бот работает! Отправь описание товара.")
                else:
                    send_message(chat_id, f"Ты написал: {text}")
    except Exception as e:
        print(f"Ошибка: {e}")
    time.sleep(1)
