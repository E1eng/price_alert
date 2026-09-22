aimport os, time, json
from decimal import Decimal
from pathlib import Path
import requests

TOKEN = os.environ["8852475575:AAGt46XKv-hvtr9v6OQEm333cnvYCW73_ZM"]
CHAT_ID = os.environ["8852475575"]
CONTRACT = os.environ.get("TOKEN_ADDRESS", "0x63ee90921eac3c3f87961c17556bb3ebdf2490a9").lower()
THRESHOLDS = [Decimal(x.strip()) for x in os.environ.get("MCAP_THRESHOLDS", "5000000,10000000,20000000").split(",") if x.strip()]
POLL_SECONDS = int(os.environ.get("POLL_SECONDS", "30"))
RUN_SECONDS = int(os.environ.get("RUN_SECONDS", "270"))
API = f"https://api.ponsapi.dev/v1/tokens/{CONTRACT}/price"
STATE_FILE = Path("state.json")

def load_state():
    try:
        return json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {"above": {}}
    except Exception:
        return {"above": {}}

def save_state(s):
    STATE_FILE.write_text(json.dumps(s))

def get_price():
    r = requests.get(API, timeout=15)
    r.raise_for_status()
    d = r.json()
    mcap = d.get("mcapUsd")
    price = d.get("priceUsd")
    if mcap is None:
        raise RuntimeError(f"No mcapUsd in API response: {d}")
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
    started = time.time()
    while time.time() - started < RUN_SECONDS:
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
