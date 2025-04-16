import os
import ccxt
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
from strategy.ema_crossover import ema_crossover_strategy
from data.fetch_data import fetch_bybit_data
import argparse
import warnings
warnings.filterwarnings("ignore")

# Load environment
load_dotenv(override=True)

# Constants
RISK_PCT = 0.02
RR_RATIO = 2  # Take Profit = 2x Stop Loss

def test_bot(symbol='BTC/USDT', timeframe='1m', capital=100, stop_loss_pct=0.02):
    print(f"\n🔄 Running test bot for {symbol} on timeframe {timeframe}...")

    # Fetch recent market data
    df = fetch_bybit_data(symbol, timeframe, limit=100)
    df = ema_crossover_strategy(df, symbol=symbol, capital=capital)

    latest_signal = df['signal'].iloc[-1]
    price = df['close'].iloc[-1]
    timestamp = df.index[-1]
    base = symbol.split('/')[0]

    # Calculate risk parameters
    risk_amount = capital * RISK_PCT
    position_size = round(capital / price, 6)
    position_value = round(position_size * price, 2)

    # Long or Short calculation
    if latest_signal == 1:
        sl_price = round(price - (risk_amount / position_size), 2)
        tp_price = round(price + ((risk_amount * RR_RATIO) / position_size), 2)
        direction = "LONG"
        potential_pnl = round((tp_price - price) * position_size, 2)
    elif latest_signal == -1:
        sl_price = round(price + (risk_amount / position_size), 2)
        tp_price = round(price - ((risk_amount * RR_RATIO) / position_size), 2)
        direction = "SHORT"
        potential_pnl = round((price - tp_price) * position_size, 2)
    else:
        sl_price = tp_price = direction = potential_pnl = None

    # Display output
    print(f"\n🕒 Timestamp: {timestamp}")
    print(f"💰 Capital: ${capital}")
    print(f"📉 Current Price: ${price}")
    print(f"📦 Position Size: {position_size} {base} (~${position_value})")

    if latest_signal != 0:
        print(f"⚠️ Stop Loss Price: ${sl_price} | 🎯 Take Profit Price: ${tp_price}")
        print(f"🧮 SL Amount: -${risk_amount:.2f} | TP Amount: +${risk_amount * RR_RATIO:.2f}")
        print(f"📊 Signal: {'🟢 BUY (LONG)' if latest_signal == 1 else '🔴 SELL (SHORT)'}")
        print(f"\n💡 Action Plan:")
        print(f"  → Enter {direction} at ${price}")
        print(f"  → Risking ${round(risk_amount, 2)} | SL: {sl_price}, TP: {tp_price}")
        print(f"  → Potential Profit: ~${potential_pnl}")
    else:
        print(f"📊 Signal: ⚪ HOLD")
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