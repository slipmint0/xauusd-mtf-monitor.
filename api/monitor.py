import os
import time
import hmac
import hashlib
import requests

def fetch_exness_candles(symbol, timeframe, limit=24):
    """Fetches candles using official cryptographic request signing required by Exness."""
    api_key_id = os.environ.get("EXNESS_API_KEY_ID")
    secret_key = os.environ.get("EXNESS_SECRET_KEY")
    
    if not api_key_id or not secret_key:
        print("API Credentials missing.")
        return None

    # Setup parameters
    host = "://exness-api.com"
    path = f"/v1/market-data/candles"
    query_params = f"symbol={symbol}&timeframe={timeframe}&limit={limit}"
    url = f"https://{host}{path}?{query_params}"
    
    timestamp = str(int(time.time() * 1000))
    method = "GET"
    
    # Construct the cryptographic signing string
    sign_string = f"{method}{timestamp}{path}{query_params}"
    
    # Generate HMAC-SHA256 Signature
    signature = hmac.new(
        secret_key.encode('utf-8'),
        sign_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    headers = {
        "EXN-API-KEY": api_key_id,
        "EXN-SIGNATURE": signature,
        "EXN-TIMESTAMP": timestamp,
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get("candles", [])
        else:
            print(f"Exness API Reject Status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Network Fault Connecting to Exness Host: {e}")
    return None

def calculate_extremes(candles):
    if not isinstance(candles, list) or len(candles) < 2:
        return None, None, None
    
    completed_candles = candles[:-1]
    current_candle = candles[-1]
    
    try:
        highs = [float(c) for c in completed_candles]
        lows = [float(c) for c in completed_candles]
        current_price = float(current_candle) 
        return max(highs), min(lows), current_price
    except Exception as e:
        print(f"Data parsing exception: {e}")
        return None, None, None

def handler(request):
    TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
    TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return {"statusCode": 500, "body": "Telegram configurations are unverified."}
        
    symbol = "XAUUSDm"  # Suffix specific to Standard accounts
    alerts = []
    
    # Check M15 Timeframe
    m15_candles = fetch_exness_candles(symbol, "15m", limit=24)
    m15_high, m15_low, current_p15 = calculate_extremes(m15_candles)
    if m15_high is not None and current_p15 is not None:
        if current_p15 >= m15_high:
            alerts.append(f"📈 **M15 HIGH Breakout!**\nPrice: ${current_p15} (Prev High: ${m15_high})")
        elif current_p15 <= m15_low:
            alerts.append(f"📉 **M15 LOW Breakout!**\nPrice: ${current_p15} (Prev Low: ${m15_low})")

    # Check M30 Timeframe
    m30_candles = fetch_exness_candles(symbol, "30m", limit=24)
    m30_high, m30_low, current_p30 = calculate_extremes(m30_candles)
    if m30_high is not None and current_p30 is not None:
        if current_p30 >= m30_high:
            alerts.append(f"📈 **M30 HIGH Breakout!**\nPrice: ${current_p30} (Prev High: ${m30_high})")
        elif current_p30 <= m30_low:
            alerts.append(f"📉 **M30 LOW Breakout!**\nPrice: ${current_p30} (Prev Low: ${m30_low})")

    # Broadcast to Telegram if verified breakouts match
    if alerts:
        # Your specific verified Exness referral portal tracking URL
        partner_link = "https://one.toexness.com/a/c_5ufq543auz"
        
        # High-converting layout template to turn alert traffic into active clients
        promo_marketing_block = (
            "\n\n⚡ **Trade this live gold move with Exness tight spreads:**\n"
            f"👉 [Open an Active Trading Account]({partner_link})"
        )
        
        compiled_message = f"🚨 **Exness Signed Live Market Alert** 🚨\n\n" + "\n\n".join(alerts) + promo_marketing_block
        
        telegram_url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID, 
            "text": compiled_message, 
            "parse_mode": "Markdown",
            "disable_web_page_preview": False
        }
        requests.post(telegram_url, json=payload, timeout=10)
        return {"statusCode": 200, "body": "Signed alerts with tracking link deployed."}
        
    return {"statusCode": 200, "body": "All metrics checked. No gold breakouts."}
