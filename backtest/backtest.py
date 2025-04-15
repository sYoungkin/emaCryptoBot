import pandas as pd
import matplotlib.pyplot as plt
from strategy.ema_crossover import ema_crossover_strategy
import os

# Ensure logs/ directory exists
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
    trades['price'] = df['close']
    trades[['position', 'price']].to_csv('logs/trades.csv')

    # Plot results
    plt.figure(figsize=(12,6))
    plt.subplot(2,1,1)
    plt.plot(df['close'], label='Close Price')
    plt.plot(df['EMA9'], label='EMA 9')
    plt.plot(df['EMA20'], label='EMA 20')
    plt.legend()
    plt.title('Price and EMAs')

    plt.subplot(2,1,2)
    plt.plot(df['equity_curve'], label='Equity Curve', color='green')
    plt.title('Equity Curve')
    plt.tight_layout()
    plt.savefig('logs/backtest_plot.png')
    plt.show()

    print(f"Total Return: ${total_return:.2f}")
    print(f"Win Rate: {win_rate:.2%}")
    print(f"Max Drawdown: {max_drawdown:.2%}")
    return df

if __name__ == "__main__":
    df = pd.read_csv("data/BTCUSDT_1h.csv", index_col="timestamp", parse_dates=True)
    backtest(df)