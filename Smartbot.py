import os
import requests
import time
import json
import re

TELEGRAM_TOKEN = "8720043003:AAFAdFvep5cKT02mzu2VG71USVwsJFrJYVc"
DEEPSEEK_API_KEY = "sk-92d2a007832043e5a482856694a2be73"  # ВСТАВЬТЕ ВАШ КЛЮЧ

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
            "temperature": 0.7
        },
        timeout=60
    )
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    return f"Ошибка API: {response.status_code}"

def analyze_market(item_name):
    prompt = f"""Ты — аналитик рынка Avito. Проанализируй товар: "{item_name}"
Ответь ТОЛЬКО JSON:
{{
    "min_price": число,
    "max_price": число,
    "avg_price": число,
    "trend": "растёт/падает/стабилен",
    "sell_time": "быстро/средне/медленно",
    "advice": "короткий совет"
}}"""
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

Правила:
- Пиши как человек, естественно и без шаблонов
- Не придумывай то, чего нет в описании
- Укажи состояние, комплектацию, ключевые особенности
- Длина: 3-4 предложения
- Не используй фразы: "торг уместен", "цена договорная", "продам в связи с переездом"

Напиши только текст описания."""
    return get_deepseek(prompt)

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    try:
        r = requests.get(url, params={"timeout": 30, "offset": offset}, timeout=35)
        return r.json().get('result', [])
    except:
        return []

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
                welcome = """🏢 SmartSell PRO — профессиональный помощник по продажам

Что я делаю:
• Анализирую рынок и даю точную цену
• Пишу продающее описание (естественно, без шаблонов)

Просто отправьте описание товара:
«Nike Air Max 90, размер 42, отличное состояние, полная комплектация»"""
                send_message(chat_id, welcome)
                continue
            
            if text:
                send_message(chat_id, "📊 Анализирую рынок и готовлю описание...")
                
                # Анализ рынка
                market = analyze_market(text)
                if market:
                    market_text = f"""📈 *Анализ рынка*

💰 Цены на Avito:
• Минимальная: {market.get('min_price', '?')} руб.
• Максимальная: {market.get('max_price', '?')} руб.
• Средняя: {market.get('avg_price', '?')} руб.

📊 Тренд: {market.get('trend', '?')}
⏱️ Скорость продажи: {market.get('sell_time', '?')}

💡 Совет: {market.get('advice', '')}"""
                    send_message(chat_id, market_text)
                else:
                    send_message(chat_id, "⚠️ Не удалось проанализировать рынок.")
                
                # Описание
                description = get_description(text)
                send_message(chat_id, f"📝 *Описание для Avito:*\n\n{description}")
                
    except Exception as e:
        print(f"Ошибка: {e}")
        time.sleep(5)
