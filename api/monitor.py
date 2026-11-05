import os
import requests

def fetch_exness_candles(symbol, timeframe, limit=20, api_key=""):
    url = f"https://exness.com{symbol}&timeframe={timeframe}&limit={limit}"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get("candles", [])
    except Exception as e:
        print(f"Error fetching {timeframe}: {e}")
    return []

def calculate_extremes(candles):
    if not candles or len(candles) < 2:
        return None, None, None
    completed_candles = candles[:-1]
    current_candle = candles[-1]
    highs = [float(c[2]) for c in completed_candles]
    lows = [float(c[3]) for c in completed_candles]
    current_price = float(current_candle[4])
    return max(highs), min(lows), current_price

def handler(request):
    EXNESS_API_KEY = os.environ.get("EXNESS_API_KEY")
    TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
    TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
    symbol = "XAUUSD"
    alerts = []
    
    m15_candles = fetch_exness_candles(symbol, "15m", limit=24, api_key=EXNESS_API_KEY)
    m15_high, m15_low, current_p15 = calculate_extremes(m15_candles)
    if m15_high and current_p15:
        if current_p15 >= m15_high:
            alerts.append(f"📈 **M15 HIGH Breakout!**\nPrice: ${current_p15} (Prev High: ${m15_high})")
        elif current_p15 <= m15_low:
            alerts.append(f"📉 **M15 LOW Breakout!**\nPrice: ${current_p15} (Prev Low: ${m15_low})")

    m30_candles = fetch_exness_candles(symbol, "30m", limit=24, api_key=EXNESS_API_KEY)
    m30_high, m30_low, current_p30 = calculate_extremes(m30_candles)
    if m30_high and current_p30:
        if current_p30 >= m30_high:
            alerts.append(f"📈 **M30 HIGH Breakout!**\nPrice: ${current_p30} (Prev High: ${m30_high})")
        elif current_p30 <= m30_low:
            alerts.append(f"📉 **M30 LOW Breakout!**\nPrice: ${current_p30} (Prev Low: ${m30_low})")

    if alerts:
        compiled_message = f"🚨 **XAUUSD Multi-Timeframe Alert** 🚨\n\n" + "\n\n".join(alerts)
        telegram_url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": compiled_message, "parse_mode": "Markdown"}
        requests.post(telegram_url, json=payload, timeout=10)
        return {"statusCode": 200, "body": "Alerts transmitted."}
        
    return {"statusCode": 200, "body": "Calculated intervals. No breakouts."}
