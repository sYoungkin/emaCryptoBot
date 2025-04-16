# File: live/bybit_bot.py
import os
import ccxt
import pandas as pd
import requests
from datetime import datetime
from dotenv import load_dotenv
from strategy.ema_crossover import ema_crossover_strategy
from archive.fetch_data_binance import fetch_binance_data  # TODO: create fetch_bybit_data if needed
import argparse

load_dotenv()

api_key = os.getenv('BYBIT_API_KEY')
api_secret = os.getenv('BYBIT_API_SECRET')
chat_id = os.getenv('TELEGRAM_CHAT_ID')
bot_token = os.getenv('TELEGRAM_TOKEN')

exchange = ccxt.bybit({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
})
exchange.set_sandbox_mode(True)

LOG_PATH = 'logs/live_trades.csv'
os.makedirs('logs', exist_ok=True)

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    requests.post(url, data=data)

def log_trade(time, symbol, action, price, amount, mode):
    df = pd.DataFrame([[time, symbol, action, price, amount, mode]],
                      columns=['timestamp', 'symbol', 'action', 'price', 'amount', 'mode'])
    if os.path.exists(LOG_PATH):
        df.to_csv(LOG_PATH, mode='a', header=False, index=False)
    else:
        df.to_csv(LOG_PATH, mode='w', header=True, index=False)

def run_live_bot(symbol='BTC/USDT', timeframe='1m', capital=100, stop_loss_pct=0.02, mode='paper'):
    df = fetch_binance_data(symbol, timeframe, limit=100)  # Replace with fetch_bybit_data later
    df = ema_crossover_strategy(df)
    latest_signal = df['signal'].iloc[-1]
    price = df['close'].iloc[-1]
    position = df['position'].iloc[-1]
    timestamp = df.index[-1]

    quote = symbol.split('/')[1]
    balance = exchange.fetch_free_balance()[quote] if mode == 'live' else capital
    risk_pct = 0.02
    risk_amount = balance * risk_pct
    stop_distance = stop_loss_pct * price
    amount = round(risk_amount / stop_distance, 6)

    message = f"[{timestamp}] {mode.upper()} MODE\n"

    open_orders = exchange.fetch_open_orders(symbol) if mode == 'live' else []
    if open_orders:
        message += "Skipping: Open orders exist."
        print(message)
        send_telegram_alert(message)
        return

    if latest_signal == 1:
        stop_price = round(price * (1 - stop_loss_pct), 2)
        take_profit_price = round(price * (1 + (stop_loss_pct * 2)), 2)
        message += f"🟢 BUY signal | {symbol} at ${price} | SL: ${stop_price} | TP: ${take_profit_price} | Qty: {amount}"

        if mode == 'live':
            # exchange.create_market_buy_order(symbol, amount)
            pass
        log_trade(timestamp, symbol, 'BUY', price, amount, mode)

    elif latest_signal == -1:
        stop_price = round(price * (1 + stop_loss_pct), 2)
        take_profit_price = round(price * (1 - (stop_loss_pct * 2)), 2)
        message += f"🔴 SELL signal | {symbol} at ${price} | SL: ${stop_price} | TP: ${take_profit_price} | Qty: {amount}"

        if mode == 'live':
            # exchange.create_market_sell_order(symbol, amount)
            pass
        log_trade(timestamp, symbol, 'SELL', price, amount, mode)

    else:
        message += f"❓ HOLD | No action for {symbol}"
        log_trade(timestamp, symbol, 'HOLD', price, 0, mode)

    print(message)
    send_telegram_alert(message)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the EMA trading bot on Bybit.")
    parser.add_argument("--symbol", default="BTC/USDT", help="Trading pair (default: BTC/USDT)")
    parser.add_argument("--timeframe", default="1m", help="Candlestick timeframe (default: 1m)")
    parser.add_argument("--capital", type=float, default=100, help="Capital used for paper mode")
    parser.add_argument("--stop", type=float, default=0.02, help="Stop loss percentage")
    parser.add_argument("--mode", default="paper", choices=["paper", "live"], help="Execution mode")
    args = parser.parse_args()

    run_live_bot(
        symbol=args.symbol,
        timeframe=args.timeframe,
        capital=args.capital,
        stop_loss_pct=args.stop,
        mode=args.mode
    )