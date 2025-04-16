import os
import ccxt
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from strategy.ema_crossover import ema_crossover_strategy
from data.fetch_data import fetch_bybit_data
import argparse
import requests

load_dotenv(override=True)

# Constants
RISK_PCT = 0.02
LOG_PATH = "logs/test_bot_log.csv"
os.makedirs("logs", exist_ok=True)

# Telegram Setup
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


def test_bot(symbol='BTC/USDT', timeframe='1m', capital=100, stop_loss_pct=0.02):
    print(f"\n🔄 Running test bot for {symbol} on timeframe {timeframe}...")

    df = fetch_bybit_data(symbol, timeframe, limit=100)
    df = ema_crossover_strategy(df, symbol=symbol, capital=capital)

    latest_signal = df['signal'].iloc[-1]
    price = df['close'].iloc[-1]
    timestamp = df.index[-1]
    position = df['position'].iloc[-1]

    base = symbol.split('/')[0]
    stop_amount = capital * stop_loss_pct
    stop_distance = stop_amount / price
    position_size = round(capital / price, 6)
    position_value = round(position_size * price, 2)

    if latest_signal == 1:  # BUY
        sl_price = round(price - stop_amount / position_size, 2)
        tp_price = round(price + stop_amount * 2 / position_size, 2)
        direction = "🟢 BUY"

    elif latest_signal == -1:  # SELL
        sl_price = round(price + stop_amount / position_size, 2)
        tp_price = round(price - stop_amount * 2 / position_size, 2)
        direction = "🔴 SELL"
    else:
        sl_price = tp_price = None
        direction = "⚪ HOLD"

    print(f"\n🕒 Timestamp: {timestamp}")
    print(f"💰 Capital: ${capital}")
    print(f"📉 Current Price: ${price}")
    print(f"📦 Position Size: {position_size} {base} (~${position_value})")
    if sl_price and tp_price:
        print(f"⚠️ Stop Loss: {sl_price} | 🎯 Take Profit: {tp_price}")
    print(f"📊 Signal: {direction}")

    # Action plan and alert (only on signal)
    if latest_signal != 0:
        potential_pnl = round(abs(tp_price - price) * position_size, 2)
        message = (
            f"{direction} Signal for {symbol}\n"
            f"Price: ${price}\n"
            f"SL: {sl_price} | TP: {tp_price}\n"
            f"Position: {position_size} {base} (~${position_value})\n"
            f"Risking ${round(stop_amount, 2)} | Potential: ${potential_pnl}"
        )
        print(f"\n💡 Action Plan:\n  → {message.replace(chr(10), chr(10)+'  → ')}")
        send_telegram_alert(message)
    else:
        print("\n💤 No action taken. Strategy suggests HOLD.")

    # Logging every run
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