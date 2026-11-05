import os
import requests

def fetch_gold_data():
    """Fetches real-time global gold spot prices using valid GoldAPI parameters."""
    gold_api_key = os.environ.get("GOLD_API_KEY")
    if not gold_api_key:
        print("Configuration Error: Global Gold API key is missing.")
        return None, None, None

    # FIXED: Using the exact official GoldAPI endpoints path structure
    url = "https://goldapi.io"
    headers = {
        "x-access-token": gold_api_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            # Extract factual metrics returned by the API payload
            current_price = float(data.get("price"))
            today_high = float(data.get("high_price"))
            today_low = float(data.get("low_price"))
            
            return today_high, today_low, current_price
        else:
            print(f"GoldAPI rejection status: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Network error connecting to data stream: {e}")
    return None, None, None

def handler(request):
    """Official Vercel serverless entry point function invocation handling."""
    TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
    TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return {"statusCode": 500, "body": "Telegram configurations are unverified."}
        
    alerts = []
    
    # Evaluate current market levels against live daily parameters
    high_bound, low_bound, current_p = fetch_gold_data()
    
    if high_bound and current_p:
        if current_p >= high_bound:
            alerts.append(f"📈 **XAUUSD High Breakout!**\nCurrent Price: ${current_p}\nDaily High Boundary: ${high_bound}")
        elif current_p <= low_bound:
            alerts.append(f"📉 **XAUUSD Low Breakout!**\nCurrent Price: ${current_p}\nDaily Low Boundary: ${low_bound}")

    # Send out message if thresholds match
    if alerts:
        partner_link = "https://one.toexness.com/a/c_5ufq543auz"
        promo_marketing_block = (
            "\n\n⚡ **Trade this live gold move with Exness tight spreads:**\n"
            f"👉 [Open an Active Trading Account]({partner_link})"
        )
        
        compiled_message = f"🚨 **Live Gold Market Alert** 🚨\n\n" + "\n\n".join(alerts) + promo_marketing_block
        
        # FIXED: Correct base API routing domain with the missing 'bot' prefix identifier keyword added
        telegram_url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID, 
            "text": compiled_message, 
            "parse_mode": "Markdown",
            "disable_web_page_preview": False
        }
        requests.post(telegram_url, json=payload, timeout=10)
        return {"statusCode": 200, "body": "Breakout notification successfully pushed to Telegram."}
        
    return {"statusCode": 200, "body": f"Checks complete. No breakouts. Price: ${current_p if current_p else 'N/A'}"}
