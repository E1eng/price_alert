import os, time, json
from decimal import Decimal
from pathlib import Path
import requests

TOKEN = "8852475575:AAGt46XKv-hvtr9v6OQEm333cnvYCW73_ZM" 
CHAT_ID = "8852475575"
CONTRACT = os.environ.get("TOKEN_ADDRESS", "0x63ee90921eac3c3f87961c17556bb3ebdf2490a9").lower()

THRESHOLDS = [Decimal(str(x)) for x in range(800_000, 10_000_000 + 1, 100_000)]
POLL_SECONDS = int(os.environ.get("POLL_SECONDS", "30"))
STATE_FILE = Path("state.json")

def load_state():
    try:
        return json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {"above": {}}
    except Exception:
        return {"above": {}}

def save_state(s):
    STATE_FILE.write_text(json.dumps(s))

def get_price():
    url = f"https://api.dexscreener.com/latest/dex/tokens/{CONTRACT}"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    d = r.json()
    
    pairs = d.get("pairs")
    if not pairs:
        raise RuntimeError("Data token belum ada di DexScreener")
        
    first_pair = pairs[0]
    
    mcap = first_pair.get("marketCap")
    if mcap is None:
        mcap = first_pair.get("fdv")
        
    price = first_pair.get("priceUsd")
    
    if mcap is None:
        raise RuntimeError("Mcap/FDV belum tersedia di API DexScreener")
        
    return Decimal(str(mcap)), Decimal(str(price)) if price is not None else None

def send_telegram(msg):
    r = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg},
        timeout=15,
    )
    r.raise_for_status()

def fmt_usd(x):
    if x >= 1_000_000_000: return f"${x/Decimal(1_000_000_000):.2f}B"
    if x >= 1_000_000: return f"${x/Decimal(1_000_000):.2f}M"
    if x >= 1_000: return f"${x/Decimal(1_000):.2f}K"
    return f"${x:.2f}"

def main():
    state = load_state()
    print("Bot berjalan 24/7. PM2 mode.")
    
    while True:
        try:
            mcap, price = get_price()
            print("MCAP:", mcap, "PRICE:", price)
            for target in THRESHOLDS:
                key = str(target)
                was_above = bool(state["above"].get(key, False))
                is_above = mcap >= target
                
                if is_above and not was_above:
                    msg = (
                        "🚨 MCAP ALERT\n\n"
                        f"Token: {CONTRACT}\n"
                        f"Market Cap: {fmt_usd(mcap)}\n"
                        f"Target: {fmt_usd(target)}\n"
                        + (f"Price: ${price:.10g}\n" if price is not None else "")
                        + "Chain: Robinhood Chain"
                    )
                    send_telegram(msg)
                    
                state["above"][key] = is_above
            save_state(state)
            
        except Exception as e:
            print("ERROR:", repr(e))
            
        time.sleep(POLL_SECONDS)

if __name__ == "__main__":
    main()
    
