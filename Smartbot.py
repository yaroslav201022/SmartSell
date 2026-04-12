import os
import requests
import time

print("Бот пытается запуститься...")

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '').strip()

print(f"Длина токена: {len(TELEGRAM_TOKEN)}")
print(f"Первые 10 символов: {TELEGRAM_TOKEN[:10] if TELEGRAM_TOKEN else 'НЕТ'}")

if not TELEGRAM_TOKEN or len(TELEGRAM_TOKEN) < 40:
    print("ОШИБКА: TELEGRAM_TOKEN не найден или слишком короткий!")
    print(f"Значение: '{TELEGRAM_TOKEN}'")
    exit(1)

print("Токен найден, проверяю соединение с Telegram...")

try:
    test_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe"
    test_response = requests.get(test_url, timeout=10)
    if test_response.status_code == 200:
        print("Соединение с Telegram успешно!")
    else:
        print(f"Ошибка соединения: {test_response.status_code}")
        exit(1)
except Exception as e:
    print(f"Ошибка при проверке токена: {e}")
    exit(1)

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
                if text == '/start':
                    requests.post(send_url, json={"chat_id": chat_id, "text": "Бот работает! Отправь описание товара."}, timeout=30)
                else:
                    requests.post(send_url, json={"chat_id": chat_id, "text": f"Ты написал: {text}"}, timeout=30)
    except Exception as e:
        print(f"Ошибка в цикле: {e}")
    time.sleep(1)
