# File: backtest/backtest_engine.py (Clean logic-only backtester)
import os
import pandas as pd
from strategy.ema_crossover import ema_crossover_strategy
import warnings
warnings.filterwarnings("ignore")

def backtest(df, symbol="BTC/USDT", initial_balance=10000, short_window=5, long_window=9, leverage=1):
    df = ema_crossover_strategy(df, symbol=symbol, short_window=short_window, long_window=long_window, capital=initial_balance)
    df['returns'] = df['close'].pct_change().fillna(0)
    df['strategy_returns'] = df['position'] * df['returns'] * leverage
    df['equity_curve'] = (1 + df['strategy_returns']).cumprod() * initial_balance

    total_return = df['equity_curve'].iloc[-1] - initial_balance
    win_rate = (df['strategy_returns'] > 0).sum() / df['strategy_returns'].count()
    max_drawdown = (df['equity_curve'] / df['equity_curve'].cummax() - 1).min()

    return df, total_return, win_rate, max_drawdown