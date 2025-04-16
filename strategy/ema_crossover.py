# File: strategy/ema_crossover.py (Cleaned and parameterized)
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")

# Defaults (can be overridden)
EMA_SHORT = 5
EMA_LONG = 9

USE_RSI = True
USE_MACD = True
USE_VWAP = True

USE_STOPLOSS = True
USE_TAKEPROFIT = True
STOPLOSS_THRESHOLD = 0.02
TAKEPROFIT_THRESHOLD = 0.04

def ema_crossover_strategy(df, symbol="BTC/USDT", short_window=EMA_SHORT, long_window=EMA_LONG, capital=10000):
    df['EMA_SHORT'] = df['close'].ewm(span=short_window, adjust=False).mean()
    df['EMA_LONG'] = df['close'].ewm(span=long_window, adjust=False).mean()

    if USE_RSI:
        df['RSI'] = compute_rsi(df['close'])
    if USE_MACD:
        df['MACD'], df['MACD_signal'] = compute_macd(df['close'])
    if USE_VWAP:
        df['VWAP'] = compute_vwap(df)

    df['signal'] = 0
    df['trade_id'] = 0
    position = 0
    entry_price = 0
    trade_id = 0
    open_trade_index = None
    trades = []

    risk_pct = 0.02
    risk_amount = capital * risk_pct

    for i in range(1, len(df)):
        ema_buy = df['EMA_SHORT'].iloc[i] > df['EMA_LONG'].iloc[i]
        ema_sell = df['EMA_SHORT'].iloc[i] < df['EMA_LONG'].iloc[i]

        price = df['close'].iloc[i]
        time = df.index[i]

        if position == 0:
            if ema_buy or ema_sell:
                position = 1 if ema_buy else -1
                entry_price = price
                stop_loss_price = entry_price * (1 - STOPLOSS_THRESHOLD) if position == 1 else entry_price * (1 + STOPLOSS_THRESHOLD)
                take_profit_price = entry_price * (1 + TAKEPROFIT_THRESHOLD) if position == 1 else entry_price * (1 - TAKEPROFIT_THRESHOLD)
                stop_distance = abs(entry_price - stop_loss_price)
                lot_size = risk_amount / stop_distance if stop_distance != 0 else 0
                reward_amount = lot_size * abs(take_profit_price - entry_price)
                df.at[time, 'signal'] = position
                df.at[time, 'trade_id'] = trade_id
                open_trade_index = time

        elif position == 1:
            stop_hit = price < stop_loss_price
            tp_hit = price > take_profit_price
            if stop_hit or tp_hit or ema_sell:
                pnl = (price - entry_price) * lot_size
                pips = (price - entry_price) * 100
                trades.append([
                    open_trade_index.strftime('%Y-%m-%d'),
                    symbol.replace('/', ''),
                    'Buy',
                    round(entry_price, 2),
                    round(stop_loss_price, 2),
                    round(take_profit_price, 2),
                    round(price, 2),
                    round(pips, 1),
                    round(risk_amount, 2),
                    round(reward_amount, 2),
                    f"1:{round(reward_amount/risk_amount, 1)}",
                    round(lot_size, 6),
                    'Win' if pnl > 0 else 'Loss'
                ])
                df.at[time, 'signal'] = -1
                df.at[time, 'trade_id'] = trade_id
                position = 0
                trade_id += 1

        elif position == -1:
            stop_hit = price > stop_loss_price
            tp_hit = price < take_profit_price
            if stop_hit or tp_hit or ema_buy:
                pnl = (entry_price - price) * lot_size
                pips = (entry_price - price) * 100
                trades.append([
                    open_trade_index.strftime('%Y-%m-%d'),
                    symbol.replace('/', ''),
                    'Sell',
                    round(entry_price, 2),
                    round(stop_loss_price, 2),
                    round(take_profit_price, 2),
                    round(price, 2),
                    round(pips, 1),
                    round(risk_amount, 2),
                    round(reward_amount, 2),
                    f"1:{round(reward_amount/risk_amount, 1)}",
                    round(lot_size, 6),
                    'Win' if pnl > 0 else 'Loss'
                ])
                df.at[time, 'signal'] = 1
                df.at[time, 'trade_id'] = trade_id
                position = 0
                trade_id += 1

    df['position'] = df['signal'].replace(to_replace=0, method='ffill').fillna(0)
    trades_df = pd.DataFrame(trades, columns=[
        'Date', 'Pair', 'Buy/Sell', 'Entry Price', 'Stop Loss', 'Take Profit',
        'Exit Price', 'Pips Gained/Lost', 'Risk (USD)', 'Reward (USD)', 'R:R Ratio', 'Lot Size', 'Result'
    ])
    trades_df.to_csv('logs/trades.csv', index=False)
    return df

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal, adjust=False).mean()
    return macd, macd_signal

def compute_vwap(df):
    return (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()


if __name__ == "__main__":
    import os

    # Temporary test — load a dataset
    df = pd.read_csv("data/BTCUSDT_1h.csv", index_col="timestamp", parse_dates=True)
    
    # Run strategy and output trades.csv
    os.makedirs("logs", exist_ok=True)
    ema_crossover_strategy(df, capital=10000)
    
    print("✅ Strategy executed and trades.csv written to logs/")