import ccxt
import pandas as pd
import time

def fetch_binance_data(symbol='BTC/USDT', timeframe='1m', limit=1000):
    exchange = ccxt.binance()
    data = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df

if __name__ == "__main__":
    df = fetch_binance_data()
    df.to_csv('data/BTCUSDT_1h.csv')
    print("Data saved to data/BTCUSDT_1h.csv")