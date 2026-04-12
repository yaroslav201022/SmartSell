print("Бот пытается запуститься...")

import os
import requests
import time

print("Библиотеки загружены")

TELEGRAM_TOKEN = os.environ.get('8720043003:AAHgZKlAMo6T63maN-oFLa4EvqTwgxiiS4g')

if not TELEGRAM_TOKEN:
    print("ОШИБКА: TELEGRAM_TOKEN не найден в переменных окружения!")
    exit(1)
else:
    print(f"Токен найден: {TELEGRAM_TOKEN[:10]}...")

print("Бот запущен и готов к работе!")

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
                requests.post(send_url, json={"chat_id": chat_id, "text": f"Ты написал: {text}"}, timeout=30)
    except Exception as e:
        print(f"Ошибка: {e}")
    time.sleep(1)
