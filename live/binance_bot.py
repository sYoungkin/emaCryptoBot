import os
import ccxt
import pandas as pd
import requests
from dotenv import load_dotenv
from strategy.ema_crossover import ema_crossover_strategy
from data.fetch_data import fetch_binance_data

load_dotenv()

api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_SECRET')
chat_id = os.getenv('TELEGRAM_CHAT_ID')
bot_token = os.getenv('TELEGRAM_TOKEN')

exchange = ccxt.binance({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True
})

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    requests.post(url, data=data)

def run_live_bot(symbol='BTC/USDT', timeframe='1h', amount=0.001, stop_loss_pct=0.02):
    df = fetch_binance_data(symbol, timeframe)
    df = ema_crossover_strategy(df)
    latest_signal = df['signal'].iloc[-1]
    price = df['close'].iloc[-1]
    position = df['position'].iloc[-1]

    balance = exchange.fetch_free_balance()['USDT']
    message = ""

    # Check current open orders to avoid duplicates
    open_orders = exchange.fetch_open_orders(symbol)
    if open_orders:
        print("Open orders exist. Skipping new trade.")
        return

    if latest_signal == 1:
        stop_price = round(price * (1 - stop_loss_pct), 2)
        message = f"BUY {symbol} at ${price} with SL at ${stop_price}"
        # exchange.create_order(symbol, 'market', 'buy', amount)
        # exchange.create_order(symbol, 'stop_loss_limit', 'sell', amount, stop_price, {'stopPrice': stop_price})
    elif latest_signal == -1:
        stop_price = round(price * (1 + stop_loss_pct), 2)
        message = f"SELL {symbol} at ${price} with SL at ${stop_price}"
        # exchange.create_order(symbol, 'market', 'sell', amount)
        # exchange.create_order(symbol, 'stop_loss_limit', 'buy', amount, stop_price, {'stopPrice': stop_price})
    else:
        message = "Signal: HOLD"

    print(message)
    send_telegram_alert(message)

if __name__ == "__main__":
    run_live_bot()