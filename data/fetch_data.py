import ccxt
import pandas as pd
import argparse
import os
import warnings
warnings.filterwarnings("ignore")

def fetch_bybit_data(symbol='BTC/USDT', timeframe='1h', limit=1000):
    exchange = ccxt.bybit()
    exchange.set_sandbox_mode(True)  # ✅ Use Bybit testnet for testing
    data = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df

def save_to_csv(pair='BTCUSDT', timeframe='1h', limit=1000, save_dir='data'):
    symbol_ccxt = pair.replace('USDT', '/USDT')
    df = fetch_bybit_data(symbol_ccxt, timeframe, limit)
    os.makedirs(save_dir, exist_ok=True)
    filepath = os.path.join(save_dir, f'{pair}_{timeframe}.csv')
    df.to_csv(filepath)
    print(f"✅ Saved: {filepath}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fetch Bybit OHLCV data and save as CSV.')
    parser.add_argument('--pair', type=str, default='BTCUSDT', help='e.g. BTCUSDT, ETHUSDT')
    parser.add_argument('--timeframe', type=str, default='1h', help='e.g. 1m, 5m, 1h, 1d')
    parser.add_argument('--limit', type=int, default=1000, help='Number of candles to fetch')
    args = parser.parse_args()

    save_to_csv(pair=args.pair, timeframe=args.timeframe, limit=args.limit)