# File: evaluate/ema_sweep_report.py
import pandas as pd
import matplotlib.pyplot as plt
import os
from strategy.ema_crossover import ema_crossover_strategy

sweep_pairs = [(5, 9), (9, 20), (10, 30), (20, 50), (50, 100)]
initial_balance = 10000
os.makedirs("logs", exist_ok=True)

results = []

for short, long in sweep_pairs:
    df = pd.read_csv("data/BTCUSDT_1h.csv", index_col="timestamp", parse_dates=True)
    df = ema_crossover_strategy(df.copy(), short_window=short, long_window=long)

    df['returns'] = df['close'].pct_change().fillna(0)
    df['strategy_returns'] = df['position'] * df['returns']
    df['equity_curve'] = (1 + df['strategy_returns']).cumprod() * initial_balance

    total_return = df['equity_curve'].iloc[-1] - initial_balance
    win_rate = (df['strategy_returns'] > 0).sum() / df['strategy_returns'].count()
    max_drawdown = (df['equity_curve'] / df['equity_curve'].cummax() - 1).min()
    num_trades = df['signal'].abs().sum() // 2

    results.append({
        'EMA_SHORT': short,
        'EMA_LONG': long,
        'Total Return': round(total_return, 2),
        'Win Rate': round(win_rate, 4),
        'Max Drawdown': round(max_drawdown, 4),
        'Trades': int(num_trades)
    })

# Save report
report_df = pd.DataFrame(results)
report_path = "logs/ema_sweep_report.csv"
report_df.to_csv(report_path, index=False)
print(f"Saved EMA sweep results to {report_path}")

# Highlight best performer
best = report_df.loc[report_df['Total Return'].idxmax()]
print("\n🏆 Best EMA Pair:")
print(best)

# Plot equity curves
plt.figure(figsize=(10, 6))
for short, long in sweep_pairs:
    df = pd.read_csv("data/BTCUSDT_1h.csv", index_col="timestamp", parse_dates=True)
    df = ema_crossover_strategy(df.copy(), short_window=short, long_window=long)
    df['returns'] = df['close'].pct_change().fillna(0)
    df['strategy_returns'] = df['position'] * df['returns']
    df['equity_curve'] = (1 + df['strategy_returns']).cumprod() * initial_balance
    label = f"EMA {short}/{long}"
    if short == best['EMA_SHORT'] and long == best['EMA_LONG']:
        plt.plot(df.index, df['equity_curve'], label=f"{label} ⭐", linewidth=2.5)
    else:
        plt.plot(df.index, df['equity_curve'], label=label, alpha=0.5)

plt.title("Equity Curve Comparison for EMA Pairs")
plt.xlabel("Time")
plt.ylabel("Equity")
plt.legend()
plt.tight_layout()
plt.savefig("logs/ema_equity_comparison.png")
print("Saved equity comparison plot to logs/ema_equity_comparison.png")
