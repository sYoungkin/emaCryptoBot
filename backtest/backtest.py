# File: backtest/backtest.py (Updated for simplified EMA strategy with indicator overlays)
import os
import pandas as pd
import matplotlib.pyplot as plt
from strategy.ema_crossover import ema_crossover_strategy, EMA_SHORT, EMA_LONG, USE_RSI, USE_MACD, USE_VWAP
import warnings
warnings.filterwarnings("ignore")

os.makedirs("logs", exist_ok=True)


def backtest(df, initial_balance=10000):
    df = ema_crossover_strategy(df)
    df['returns'] = df['close'].pct_change().fillna(0)
    df['strategy_returns'] = df['position'] * df['returns']
    df['equity_curve'] = (1 + df['strategy_returns']).cumprod() * initial_balance

    total_return = df['equity_curve'].iloc[-1] - initial_balance
    win_rate = (df['strategy_returns'] > 0).sum() / df['strategy_returns'].count()
    max_drawdown = (df['equity_curve'] / df['equity_curve'].cummax() - 1).min()

    trades = pd.read_csv('logs/trades.csv') if os.path.exists('logs/trades.csv') else pd.DataFrame()

    # Plotting
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
    ax1, ax2, ax3 = axes

    ax1.plot(df.index, df['close'], label='Close', alpha=0.6)
    ax1.plot(df.index, df['EMA_SHORT'], label=f'EMA {EMA_SHORT}')
    ax1.plot(df.index, df['EMA_LONG'], label=f'EMA {EMA_LONG}')

    if USE_VWAP and 'VWAP' in df.columns:
        ax1.plot(df.index, df['VWAP'], label='VWAP', linestyle='--', alpha=0.5)

    for i, row in trades.iterrows():
        entry_time, exit_time = pd.to_datetime(row['entry_time']), pd.to_datetime(row['exit_time'])
        if row['entry_price'] < row['exit_price']:  # long
            ax1.plot(entry_time, row['entry_price'], marker='^', color='green', markersize=8)
            ax1.plot(exit_time, row['exit_price'], marker='v', color='red', markersize=8)
        else:  # short
            ax1.plot(entry_time, row['entry_price'], marker='v', color='red', markersize=8)
            ax1.plot(exit_time, row['exit_price'], marker='^', color='green', markersize=8)

    # Add dummy markers for legend
    ax1.plot([], [], marker='^', color='green', linestyle='None', label='Buy Signal')
    ax1.plot([], [], marker='v', color='red', linestyle='None', label='Sell Signal')

    ax1.set_title(f'Price with EMA {EMA_SHORT}/{EMA_LONG} and Trade Markers')
    ax1.legend()

    if USE_RSI and 'RSI' in df.columns:
        ax2.plot(df.index, df['RSI'], label='RSI', color='purple')
        ax2.axhline(70, linestyle='--', color='red', alpha=0.4)
        ax2.axhline(30, linestyle='--', color='green', alpha=0.4)
        ax2.set_title('RSI')
        ax2.legend()
    else:
        ax2.set_visible(False)

    if USE_MACD and 'MACD' in df.columns:
        ax3.plot(df.index, df['MACD'], label='MACD', color='blue')
        ax3.plot(df.index, df['MACD_signal'], label='Signal Line', color='orange')
        ax3.axhline(0, linestyle='--', color='black', alpha=0.4)
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