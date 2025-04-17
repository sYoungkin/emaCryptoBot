#!/usr/bin/env PYTHONWARNINGS="ignore::urllib3.exceptions.NotOpenSSLWarning" python

# File: live/bybit_bot_test_stateful.py

import os
import json
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from strategy.ema_crossover import ema_crossover_strategy
from data.fetch_data import fetch_bybit_data
import argparse
import requests

load_dotenv(override=True)

RISK_PCT = 0.02
LOG_DIR = "logs/test_bot_log_stateful"
STATE_FILE = os.path.join(LOG_DIR, "bot_state.json")

os.makedirs(LOG_DIR, exist_ok=True)
today_str = datetime.now().strftime("%Y-%m-%d")
LOG_PATH = os.path.join(LOG_DIR, f"{today_str}.csv")

chat_id = os.getenv("TELEGRAM_CHAT_ID")
bot_token = os.getenv("TELEGRAM_TOKEN")

def send_telegram_alert(message):
    if not chat_id or not bot_token:
        print("⚠️ Telegram not configured.")
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("❌ Telegram error:", str(e))

def log_to_csv(data: dict):
    df = pd.DataFrame([data])
    if os.path.exists(LOG_PATH):
        df.to_csv(LOG_PATH, mode='a', header=False, index=False)
    else:
        df.to_csv(LOG_PATH, mode='w', header=True, index=False)

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"position": 0, "entry_price": 0.0, "timestamp": None}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

def test_bot(symbol='BTC/USDT', timeframe='1m', capital=100, stop_loss_pct=0.02):
    print(f"\n🔄 Running test bot for {symbol} on timeframe {timeframe}...")

    df = fetch_bybit_data(symbol, timeframe, limit=100)
    if df is None or df.empty:
        print("⚠️ No data fetched.")
        return

    df = ema_crossover_strategy(df, symbol=symbol, capital=capital)
    if 'signal' not in df.columns:
        print("⚠️ Strategy did not return 'signal' column.")
        return

    state = load_state()
    latest_signal = df['signal'].iloc[-1]
    price = df['close'].iloc[-1]
    timestamp = df.index[-1]
    base = symbol.split('/')[0]
    stop_amount = capital * stop_loss_pct
    position_size = round(capital / price, 6)
    position_value = round(position_size * price, 2)

    # Initialize variables
    sl_price = tp_price = sl_usd = tp_usd = None
    direction = "⚪ HOLD"

    print("before if "+ str(state))

    #latest_signal = 1

    if state['position'] == 0 and latest_signal != 0:
        state['position'] = int(latest_signal)
        state['entry_price'] = float(price)
        state['timestamp'] = str(timestamp)
        print("latest !=0 and pos=0 "+str(state))
        


        if latest_signal == 1:
            sl_price = round(price - stop_amount, 2)
            tp_price = round(price + (stop_amount * 2), 2)
            direction = "🟢 BUY"
        elif latest_signal == -1:
            sl_price = round(price + stop_amount, 2)
            tp_price = round(price - (stop_amount * 2), 2)
            direction = "🔴 SELL"

        sl_usd = abs(price - sl_price) * position_size
        tp_usd = abs(tp_price - price) * position_size

        message = (
            f"{direction} Signal for {symbol}\n"
            f"Price: ${price}\n"
            f"SL: {sl_price} (-${round(sl_usd, 2)}) | TP: {tp_price} (+${round(tp_usd, 2)})\n"
            f"Position: {position_size} {base} (~${position_value})\n"
            f"Risking ${round(stop_amount, 2)} | Potential: ${round(tp_usd, 2)}"
        )
        print(f"\n💡 Action Plan:\n  → {message.replace(chr(10), chr(10)+'  → ')}")
        send_telegram_alert(message)  # Uncomment if ready

    elif state['position'] != 0:
        entry_price = float(state['entry_price'])
        if state['position'] == 1:
            sl_price = entry_price - stop_amount
            tp_price = entry_price + stop_amount * 2
            if price <= sl_price or price >= tp_price:
                print(f"✅ Closing LONG at ${price}")
                state = {"position": 0, "entry_price": 0.0, "timestamp": None}
        elif state['position'] == -1:
            sl_price = entry_price + stop_amount
            tp_price = entry_price - stop_amount * 2
            if price >= sl_price or price <= tp_price:
                print(f"✅ Closing SHORT at ${price}")
                state = {"position": 0, "entry_price": 0.0, "timestamp": None}
    else:
        print("💤 HOLD — No action taken.")

    print("before save "+str(state))
    save_state(state)

    # Log every run
    log_data = {
        "timestamp": timestamp,
        "symbol": symbol,
        "price": price,
        "signal": direction,
        "position_size": position_size,
        "position_value": position_value,
        "stop_loss": sl_price,
        "take_profit": tp_price
    }
    log_to_csv(log_data)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the test EMA trading bot on Bybit.")
    parser.add_argument("--symbol", default="BTC/USDT", help="Trading pair (default: BTC/USDT)")
    parser.add_argument("--timeframe", default="1m", help="Candlestick timeframe (default: 1m)")
    parser.add_argument("--capital", type=float, default=100, help="Capital used for paper mode")
    parser.add_argument("--stop", type=float, default=0.02, help="Stop loss percentage")
    args = parser.parse_args()

    test_bot(
        symbol=args.symbol,
        timeframe=args.timeframe,
        capital=args.capital,
        stop_loss_pct=args.stop
    )