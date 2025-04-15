# File: strategy/ema_crossover.py (Simplified EMA-only strategy with full features)
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")

# Configurable EMA windows
EMA_SHORT = 5
EMA_LONG = 9

USE_RSI = True
USE_MACD = True
USE_VWAP = True

USE_STOPLOSS = True
USE_TAKEPROFIT = True
STOPLOSS_THRESHOLD = 0.02
TAKEPROFIT_THRESHOLD = 0.04


def ema_crossover_strategy(df, short_window=EMA_SHORT, long_window=EMA_LONG):
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

    for i in range(1, len(df)):
        ema_buy = df['EMA_SHORT'].iloc[i] > df['EMA_LONG'].iloc[i]
        ema_sell = df['EMA_SHORT'].iloc[i] < df['EMA_LONG'].iloc[i]

        price = df['close'].iloc[i]

        # Entry
        if position == 0:
            if ema_buy:
                df.at[df.index[i], 'signal'] = 1
                df.at[df.index[i], 'trade_id'] = trade_id
                entry_price = price
                open_trade_index = df.index[i]
                position = 1
            elif ema_sell:
                df.at[df.index[i], 'signal'] = -1
                df.at[df.index[i], 'trade_id'] = trade_id
                entry_price = price
                open_trade_index = df.index[i]
                position = -1

        # Long exit
        elif position == 1:
            stop_loss_hit = price < entry_price * (1 - STOPLOSS_THRESHOLD) if USE_STOPLOSS else False
            take_profit_hit = price > entry_price * (1 + TAKEPROFIT_THRESHOLD) if USE_TAKEPROFIT else False
            crossover_exit = ema_sell
            if stop_loss_hit or take_profit_hit or crossover_exit:
                df.at[df.index[i], 'signal'] = -1
                df.at[df.index[i], 'trade_id'] = trade_id
                pnl = price - entry_price
                trades.append([trade_id, open_trade_index, df.index[i], entry_price, price, pnl])
                position = 0
                trade_id += 1

        # Short exit
        elif position == -1:
            stop_loss_hit = price > entry_price * (1 + STOPLOSS_THRESHOLD) if USE_STOPLOSS else False
            take_profit_hit = price < entry_price * (1 - TAKEPROFIT_THRESHOLD) if USE_TAKEPROFIT else False
            crossover_exit = ema_buy
            if stop_loss_hit or take_profit_hit or crossover_exit:
                df.at[df.index[i], 'signal'] = 1
                df.at[df.index[i], 'trade_id'] = trade_id
                pnl = entry_price - price
                trades.append([trade_id, open_trade_index, df.index[i], entry_price, price, pnl])
                position = 0
                trade_id += 1

    df['position'] = df['signal'].replace(to_replace=0, method='ffill').fillna(0)
    trades_df = pd.DataFrame(trades, columns=['trade_id', 'entry_time', 'exit_time', 'entry_price', 'exit_price', 'pnl'])
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


def detect_fvg(df):
    fvg = (df['low'].shift(-2) > df['high'])
    return fvg.astype(int)