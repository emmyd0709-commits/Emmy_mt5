import os, time, requests, yfinance as yf
from flask import Flask
from threading import Thread

app = Flask(__name__)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

PAIRS = {
    "EURUSD OTC": "EURUSD=X",
    "GBPUSD OTC": "GBPUSD=X", 
    "USDJPY OTC": "JPY=X",
    "AUDUSD OTC": "AUDUSD=X",
    "XAUUSD": "GC=F",
    "BTCUSD OTC": "BTC-USD"
}

def get_signal(sym):
    try:
        df = yf.download(sym, period="1d", interval="1m", progress=False, auto_adjust=True)
        if len(df) < 21: return "UP ⬆️"
        c = df['Close'].iloc[-1].item()
        e = df['Close'].ewm(span=20).mean().iloc[-1].item()
        return "UP ⬆️" if c > e else "DOWN ⬇️"
    except: return "UP ⬆️"

def send_menu(chat_id):
    rows = [[{"text": k, "callback_data": k}] for k in PAIRS.keys()]
    kb = {"inline_keyboard": rows}
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": chat_id, "text": "📊 *POCKET OPTION BOT*\n\nChoose Market 👇", "parse_mode": "Markdown", "reply_markup": kb})

def bot():
    print("BOT LOOP STARTED - Waiting for /start", flush=True)
    off = 0
    while True:
        try:
            r = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={off}&timeout=30", timeout=35).json()
            for u in r.get("result", []):
                off = u["update_id"] + 1
                if "message" in u and "/start" in u["message"].get("text",""):
                    send_menu(u["message"]["chat"]["id"])
                if "callback_query" in u:
                    cb = u["callback_query"]; cid = cb["message"]["chat"]["id"]
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery", json={"callback_query_id": cb["id"]})
                    sig = get_signal(PAIRS[cb["data"]])
                    txt = f"*{cb['data']}* - {sig}\n\n👉 ENTER NOW\n⏳ Expiry: 1 MIN"
                    kb = {"inline_keyboard": [[{"text": "↩️ Markets", "callback_data": "MENU"}]]}
                    if cb["data"] == "MENU":
                        send_menu(cid)
                    else:
                        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": cid, "text": txt, "parse_mode": "Markdown", "reply_markup": {"inline_keyboard": [[{"text":"↩️ Back","callback_data":"MENU"}]]}})
        except Exception as e:
            print(f"Bot error: {e}", flush=True); time.sleep(3)

Thread(target=bot, daemon=True).start()

@app.route("/")
def home(): return "Bot is Live - BOT LOOP STARTED"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
