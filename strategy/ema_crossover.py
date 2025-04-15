# File: strategy/ema_crossover.py (with trade logging)
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")

USE_RSI = False
USE_MACD = False
USE_VWAP = False
USE_VERBOSE = True
USE_RSI_EXIT = True
USE_STOPLOSS = True
USE_TAKEPROFIT = True

STOPLOSS_THRESHOLD = 0.02
TAKEPROFIT_THRESHOLD = 0.04


def ema_crossover_strategy(df, short_window=9, long_window=20):
    df['EMA9'] = df['close'].ewm(span=short_window, adjust=False).mean()
    df['EMA20'] = df['close'].ewm(span=long_window, adjust=False).mean()

    if USE_RSI or USE_RSI_EXIT:
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
        ema_buy = df['EMA9'].iloc[i] > df['EMA20'].iloc[i]
        ema_sell = df['EMA9'].iloc[i] < df['EMA20'].iloc[i]

        rsi_buy = df['RSI'].iloc[i] < 40 if USE_RSI else True
        rsi_sell = df['RSI'].iloc[i] > 60 if USE_RSI else True

        macd_buy = df['MACD'].iloc[i] > df['MACD_signal'].iloc[i] if USE_MACD else True
        macd_sell = df['MACD'].iloc[i] < df['MACD_signal'].iloc[i] if USE_MACD else True

        # Entry
        if position == 0:
            if ema_buy and rsi_buy and macd_buy:
                df.at[df.index[i], 'signal'] = 1
                df.at[df.index[i], 'trade_id'] = trade_id
                entry_price = df['close'].iloc[i]
                open_trade_index = df.index[i]
                position = 1
            elif ema_sell and rsi_sell and macd_sell:
                df.at[df.index[i], 'signal'] = -1
                df.at[df.index[i], 'trade_id'] = trade_id
                entry_price = df['close'].iloc[i]
                open_trade_index = df.index[i]
                position = -1

        # Long exit
        elif position == 1:
            exit_price = df['close'].iloc[i]
            stop_loss_hit = exit_price < entry_price * (1 - STOPLOSS_THRESHOLD) if USE_STOPLOSS else False
            take_profit_hit = exit_price > entry_price * (1 + TAKEPROFIT_THRESHOLD) if USE_TAKEPROFIT else False
            rsi_exit = df['RSI'].iloc[i] > 70 if USE_RSI_EXIT else False
            if stop_loss_hit or take_profit_hit or rsi_exit:
                df.at[df.index[i], 'signal'] = -1
                df.at[df.index[i], 'trade_id'] = trade_id
                pnl = exit_price - entry_price
                trades.append([trade_id, open_trade_index, df.index[i], entry_price, exit_price, pnl])
                position = 0
                trade_id += 1

        # Short exit
        elif position == -1:
            exit_price = df['close'].iloc[i]
            stop_loss_hit = exit_price > entry_price * (1 + STOPLOSS_THRESHOLD) if USE_STOPLOSS else False
            take_profit_hit = exit_price < entry_price * (1 - TAKEPROFIT_THRESHOLD) if USE_TAKEPROFIT else False
            rsi_exit = df['RSI'].iloc[i] < 30 if USE_RSI_EXIT else False
            if stop_loss_hit or take_profit_hit or rsi_exit:
                df.at[df.index[i], 'signal'] = 1
                df.at[df.index[i], 'trade_id'] = trade_id
                pnl = entry_price - exit_price
                trades.append([trade_id, open_trade_index, df.index[i], entry_price, exit_price, pnl])
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
