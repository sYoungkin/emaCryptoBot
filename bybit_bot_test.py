# File: live/bybit_bot_test.py
import os
import ccxt
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from strategy.ema_crossover import ema_crossover_strategy
from data.fetch_data import fetch_bybit_data  # this should be your live spot fetch
import argparse

load_dotenv()

# Load API keys (not used here but kept for later)
api_key = os.getenv('BYBIT_API_KEY')
api_secret = os.getenv('BYBIT_API_SECRET')

# Constants
RISK_PCT = 0.02

def test_bot(symbol='BTC/USDT', timeframe='1m', capital=100, stop_loss_pct=0.02):
    print(f"\n🔄 Running test bot for {symbol} on timeframe {timeframe}...")

    # Fetch recent market data
    df = fetch_bybit_data(symbol, timeframe, limit=100)
    df = ema_crossover_strategy(df, symbol=symbol, capital=capital)

    latest_signal = df['signal'].iloc[-1]
    close_price = df['close'].iloc[-1]
    timestamp = df.index[-1]
    position = df['position'].iloc[-1]

    # Position sizing logic
    stop_distance = stop_loss_pct * close_price
    risk_amount = capital * RISK_PCT
    amount = round(risk_amount / stop_distance, 6)
    tp_price = round(close_price * (1 + stop_loss_pct * 2), 2)
    sl_price = round(close_price * (1 - stop_loss_pct), 2)

    # Print results
    print(f"\n🕒 Timestamp: {timestamp}")
    print(f"💰 Capital: ${capital}")
    print(f"📉 Current Price: ${close_price}")
    print(f"⚠️ Stop Loss: {sl_price} | 🎯 Take Profit: {tp_price}")
    print(f"📦 Position Size: {amount} {symbol.split('/')[0]}")
    print(f"📊 Signal: {'🟢 BUY' if latest_signal == 1 else '🔴 SELL' if latest_signal == -1 else '⚪ HOLD'}")

    if latest_signal != 0:
        print(f"\n💡 Action Plan:")
        print(f"  → {'Enter LONG' if latest_signal == 1 else 'Enter SHORT'} at ${close_price}")
        print(f"  → Risking 2% = ${risk_amount}, SL at {sl_price}, TP at {tp_price}")
        print(f"  → Potential PnL: ~${round((tp_price - close_price) * amount, 2)}")
    else:
        print("\n💤 No action taken. Strategy suggests HOLD.")

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