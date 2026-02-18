import ccxt
import pandas as pd
import ta
import time
from telegram import Bot

# ================= CONFIG =================
import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

CAPITAL = 1000
RISK_PERCENT = 0.01       # 1%
TP_PERCENT = 0.008        # 0.8%
SL_PERCENT = 0.004        # 0.4%

PAIRS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT"]
TIMEFRAMES = ["1m", "5m"]

exchange = ccxt.binance()
bot = Bot(token=TELEGRAM_TOKEN)

waiting_validation = False

# ================= FUNCTIONS =================
def send(msg):
    bot.send_message(chat_id=CHAT_ID, text=msg)

def position_size(entry):
    risk_amount = CAPITAL * RISK_PERCENT
    sl_distance = entry * SL_PERCENT
    qty = risk_amount / sl_distance
    return round(qty, 4)

def fetch_df(symbol, tf):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=100)
    df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
    return df

def analyze(symbol, tf):
    global waiting_validation
    if waiting_validation:
        return

    df = fetch_df(symbol, tf)
    df['rsi'] = ta.momentum.RSIIndicator(df['c'], 14).rsi()
    df['ema9'] = ta.trend.EMAIndicator(df['c'], 9).ema_indicator()
    df['ema21'] = ta.trend.EMAIndicator(df['c'], 21).ema_indicator()

    last = df.iloc[-1]
    prev = df.iloc[-2]
    price = last['c']

    # BUY
    if prev['ema9'] < prev['ema21'] and last['ema9'] > last['ema21'] and last['rsi'] < 35:
        tp = price * (1 + TP_PERCENT)
        sl = price * (1 - SL_PERCENT)
        qty = position_size(price)

        send(
            f"🟢 BUY SIGNAL {symbol}
"
            f"TF: {tf}
"
            f"Entrée: {price:.2f}
"
            f"TP: {tp:.2f}
"
            f"SL: {sl:.2f}
"
            f"Taille: {qty}

"
            f"✅ Réponds: OK
❌ ou: NO"
        )
        waiting_validation = True

    # SELL
    if prev['ema9'] > prev['ema21'] and last['ema9'] < last['ema21'] and last['rsi'] > 65:
        tp = price * (1 - TP_PERCENT)
        sl = price * (1 + SL_PERCENT)
        qty = position_size(price)

        send(
            f"🔴 SELL SIGNAL {symbol}
"
            f"TF: {tf}
"
            f"Entrée: {price:.2f}
"
            f"TP: {tp:.2f}
"
            f"SL: {sl:.2f}
"
            f"Taille: {qty}

"
            f"✅ Réponds: OK
❌ ou: NO"
        )
        waiting_validation = True

# ================= START =================
send("🤖 Bot Scalping Multi-Paires démarré
Mode: Validation Manuelle")

while True:
    try:
        for tf in TIMEFRAMES:
            for pair in PAIRS:
                analyze(pair, tf)
                time.sleep(2)
        time.sleep(30)
    except Exception as e:
        send(f"⚠️ Erreur: {e}")
        time.sleep(60)
