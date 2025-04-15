# trading-bot: VWAP Toggle Fix in Backtest

# File: backtest/backtest.py
import warnings
warnings.filterwarnings("ignore")
import os
import pandas as pd
import matplotlib.pyplot as plt
from strategy.ema_crossover import ema_crossover_strategy, USE_RSI, USE_MACD, USE_VWAP

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

def backtest(df, initial_balance=10000):
    df = ema_crossover_strategy(df)
    df['returns'] = df['close'].pct_change().fillna(0)
    df['strategy_returns'] = df['position'] * df['returns']
    df['equity_curve'] = (1 + df['strategy_returns']).cumprod() * initial_balance

    # Calculate metrics
    total_return = df['equity_curve'].iloc[-1] - initial_balance
    win_rate = (df['strategy_returns'] > 0).sum() / df['strategy_returns'].count()
    max_drawdown = (df['equity_curve'] / df['equity_curve'].cummax() - 1).min()

    # Log trades
    trades = df[df['position'].diff() != 0].copy()
    trades['timestamp'] = trades.index
    trades['price'] = df['close']
    trades[['timestamp', 'position', 'price']].to_csv('logs/trades.csv', index=False)

    if trades.empty:
        print("No trades found – try adjusting strategy conditions.")

    # Plot results
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
    ax1, ax2, ax3 = axes

    ax1.plot(df.index, df['close'], label='Close', alpha=0.7)
    ax1.plot(df.index, df['EMA9'], label='EMA 9')
    ax1.plot(df.index, df['EMA20'], label='EMA 20')

    if USE_VWAP and 'VWAP' in df.columns:
        ax1.plot(df.index, df['VWAP'], label='VWAP', linestyle='--', alpha=0.5)

    if not trades.empty:
        for i, row in trades.iterrows():
            if row['position'] == 1:
                ax1.plot(row['timestamp'], row['price'], marker='^', color='green', markersize=10, label='Buy' if i == trades.index[0] else "")
            elif row['position'] == -1:
                ax1.plot(row['timestamp'], row['price'], marker='v', color='red', markersize=10, label='Sell' if i == trades.index[0] else "")

    ax1.set_title('Price, EMAs' + (', VWAP' if USE_VWAP else '') + ' with Trade Signals')
    ax1.legend()

    if USE_RSI:
        ax2.plot(df.index, df['RSI'], label='RSI', color='purple')
        ax2.axhline(70, color='red', linestyle='--', linewidth=0.5)
        ax2.axhline(30, color='green', linestyle='--', linewidth=0.5)
        ax2.set_title('RSI')
        ax2.legend()
    else:
        ax2.set_visible(False)

    if USE_MACD:
        ax3.plot(df.index, df['MACD'], label='MACD', color='blue')
        ax3.plot(df.index, df['MACD_signal'], label='Signal Line', color='orange')
        ax3.axhline(0, color='black', linestyle='--', linewidth=0.5)
        ax3.set_title('MACD')
        ax3.legend()
    else:
        ax3.set_visible(False)

    plt.tight_layout()
    plt.savefig('logs/backtest_plot.png')

    print(f"Total Return: ${total_return:.2f}")
    print(f"Win Rate: {win_rate:.2%}")
    print(f"Max Drawdown: {max_drawdown:.2%}")
    print("Plot saved to logs/backtest_plot.png")
    return df

if __name__ == "__main__":
    df = pd.read_csv("data/BTCUSDT_1h.csv", index_col="timestamp", parse_dates=True)
    backtest(df)