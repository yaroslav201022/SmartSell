import os
import requests
import time

TELEGRAM_TOKEN = "8720043003:AAFAdFvep5cKT02mzu2VG71USVwsJFrJYVc"

print("Бот запущен!")

last_id = None
while True:
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        updates = requests.get(url, params={"timeout": 30, "offset": last_id}, timeout=35).json()
        
        for update in updates.get('result', []):
            last_id = update['update_id'] + 1
            msg = update.get('message')
            if msg and msg.get('text'):
                chat_id = msg['chat']['id']
                text = msg['text']
                
                send_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                if text == '/start':
                    requests.post(send_url, json={"chat_id": chat_id, "text": "Бот работает! Отправь описание товара."}, timeout=30)
                else:
                    requests.post(send_url, json={"chat_id": chat_id, "text": f"Ты написал: {text}"}, timeout=30)
    except Exception as e:
        print(f"Ошибка: {e}")
    time.sleep(1)
