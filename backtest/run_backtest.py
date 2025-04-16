# File: backtest/run_backtest.py
import argparse
import os
import pandas as pd
from backtest.backtest_engine import backtest


def main():
    parser = argparse.ArgumentParser(description="Run EMA backtest on historical data")
    parser.add_argument('--pair', type=str, default="BTCUSDT", help="Symbol (e.g., BTCUSDT)")
    parser.add_argument('--timeframe', type=str, default="1h", help="Timeframe (e.g., 1m, 1h)")
    parser.add_argument('--ema_short', type=int, default=5, help="Short EMA window")
    parser.add_argument('--ema_long', type=int, default=9, help="Long EMA window")
    parser.add_argument('--capital', type=float, default=10000, help="Initial capital")
    parser.add_argument('--leverage', type=int, default=1, help="Leverage multiplier")
    args = parser.parse_args()

    filename = f"data/{args.pair}_{args.timeframe}.csv"
    if not os.path.exists(filename):
        print(f"❌ Data not found: {filename}")
        return

    df = pd.read_csv(filename, index_col="timestamp", parse_dates=True)
    df, total_return, win_rate, max_dd = backtest(
        df,
        symbol=args.pair.replace("USDT", "/USDT"),
        initial_balance=args.capital,
        short_window=args.ema_short,
        long_window=args.ema_long,
        leverage=args.leverage
    )

    print("\n✅ Backtest Complete")
    print(f"Pair: {args.pair} | Timeframe: {args.timeframe}")
    print(f"EMA: {args.ema_short}/{args.ema_long} | Capital: ${args.capital} | Leverage: {args.leverage}x\n")
    print(f"📈 Total Return: ${total_return:.2f}")
    print(f"🏆 Win Rate: {win_rate:.2%}")
    print(f"📉 Max Drawdown: {max_dd:.2%}")

    df.to_csv("logs/backtest_output.csv")
    print("\n📁 Output saved to logs/backtest_output.csv")
    print("📁 Trades saved to logs/trades.csv\n")

if __name__ == "__main__":
    main()