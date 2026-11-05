import os
import requests

def fetch_exness_candles(symbol, timeframe, limit=24, api_key=""):
    """Fetches real-time data and strictly verifies its existence before proceeding."""
    url = f"https://exness.com{symbol}&timeframe={timeframe}&limit={limit}"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"API Error: Server returned status code {response.status_code}")
            return None
        
        data = response.json()
        if not isinstance(data, dict) or "candles" not in data:
            print(f"Data Validation Error: Unexpected API response format for {timeframe}.")
            return None
            
        return data.get("candles", [])
    except Exception as e:
        print(f"Network Connection Error fetching {timeframe}: {e}")
    return None

def calculate_extremes(candles):
    """Calculates boundaries with absolute verification. Zero assumptions allowed."""
    # Check if candles data is valid and contains enough elements
    if candles is None or not isinstance(candles, list) or len(candles) < 2:
        print("Calculation Aborted: Insufficient or corrupted historical candle data.")
        return None, None, None
    
    completed_candles = candles[:-1]
    current_candle = candles[-1]
    
    try:
        # Strictly verify that data values are numeric arrays before evaluating min/max
        highs = [float(c[2]) for c in completed_candles if len(c) > 2 and str(c[2]).replace('.','',1).isdigit()]
        lows = [float(c[3]) for c in completed_candles if len(c) > 3 and str(c[3]).replace('.','',1).isdigit()]
        current_price = float(current_candle[4]) # Explicit close price index
        
        if not highs or not lows:
            print("Calculation Aborted: Valid historical High/Low values could not be extracted.")
            return None, None, None
            
        return max(highs), min(lows), current_price
    except Exception as e:
        print(f"Calculation Parsing Error: {e}")
        return None, None, None

def handler(request):
    # Fetch environment configurations
    EXNESS_API_KEY = os.environ.get("EXNESS_API_KEY")
    TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
    TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
    
    # Absolute confirmation required for vital system environment variables
    if not EXNESS_API_KEY or not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return {"statusCode": 500, "body": "Configuration Error: Security tokens are unverified or missing."}
        
    symbol = "XAUUSD"
    alerts = []
    
    # 1. Evaluate M15 Data
    m15_candles = fetch_exness_candles(symbol, "15m", limit=24, api_key=EXNESS_API_KEY)
    m15_high, m15_low, current_p15 = calculate_extremes(m15_candles)
    
    if m15_high is not None and current_p15 is not None:
        if current_p15 >= m15_high:
            alerts.append(f"📈 **M15 HIGH Breakout!**\nPrice: ${current_p15} (Confirmed Prev High: ${m15_high})")
        elif current_p15 <= m15_low:
            alerts.append(f"📉 **M15 LOW Breakout!**\nPrice: ${current_p15} (Confirmed Prev Low: ${m15_low})")

    # 2. Evaluate M30 Data
    m30_candles = fetch_exness_candles(symbol, "30m", limit=24, api_key=EXNESS_API_KEY)
    m30_high, m30_low, current_p30 = calculate_extremes(m30_candles)
    
    if m30_high is not None and current_p30 is not None:
        if current_p30 >= m30_high:
            alerts.append(f"📈 **M30 HIGH Breakout!**\nPrice: ${current_p30} (Confirmed Prev High: ${m30_high})")
        elif current_p30 <= m30_low:
            alerts.append(f"📉 **M30 LOW Breakout!**\nPrice: ${current_p30} (Confirmed Prev Low: ${m30_low})")

    # 3. Dispatches Telegram notification ONLY if hard breakout facts are confirmed
    if alerts:
        compiled_message = f"🚨 **XAUUSD Factual Multi-Timeframe Alert** 🚨\n\n" + "\n\n".join(alerts)
        telegram_url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": compiled_message, "parse_mode": "Markdown"}
        try:
            requests.post(telegram_url, json=payload, timeout=10)
            return {"statusCode": 200, "body": "Verified alerts transmitted successfully."}
        except Exception as e:
            return {"statusCode": 500, "body": f"Failed to deliver uncompromised data alert: {e}"}
        
    return {"statusCode": 200, "body": "Data checks passed completely. No real threshold breakouts detected."}
