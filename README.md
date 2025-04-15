# EMA-Based Trading Strategy Bot

This is a lightweight, modular backtesting engine for an EMA-crossover trading strategy, with optional RSI, MACD, and VWAP overlays for reference.

## Features

- 📈 EMA crossover-based entry and exit logic
- ✅ Optional stop loss and take profit thresholds
- 📉 RSI, MACD, and VWAP indicators (for visual analysis only)
- 🔁 Batch sweep of multiple EMA pairs
- 📊 Equity curve comparison
- 📄 Trade log output with PnL
- 📷 Auto-generated plots of price and indicators with trade markers

---

## Project Structure

```
strategy/
└── ema_crossover.py         # Core strategy logic (configurable)

backtest/
└── backtest.py              # Single EMA backtest + chart output

evaluate/
└── ema_sweep_report.py      # Batch test over multiple EMA pairs

data/
└── BTCUSDT_1h.csv           # Example dataset (Binance 1h candles)

logs/
├── trades.csv               # Auto-saved trade log
├── backtest_plot.png        # Plot from latest run
├── ema_sweep_report.csv     # Multi-pair sweep results
└── ema_equity_comparison.png # Equity curve plot
```

---

## How to Run

### Backtest a single pair (default 5/9):
```bash
python -m backtest.backtest
```

### Batch test multiple EMA pairs:
```bash
python -m evaluate.ema_sweep_report
```

---

## Strategy Logic
- **Buy entry**: EMA_SHORT crosses above EMA_LONG
- **Sell entry**: EMA_SHORT crosses below EMA_LONG
- **Exits** (long or short):
  - Stop Loss hit (2% default)
  - Take Profit hit (4% default)
  - Reverse EMA crossover

All trades are logged to `logs/trades.csv`.

---

## Example Output
```
Total Return:     $280.79
Win Rate:         52.50%
Max Drawdown:     -0.54%
```

---

## Next Steps
- Add live trading execution
- Add more indicators (Bollinger Bands, Supertrend, etc.)
- Add parameter optimization for thresholds
- REST API / Streamlit dashboard

---

## Author
This bot was co-developed and iterated using Python, Pandas, and Matplotlib — fully automated by ChatGPT.

---

Happy backtesting! 📊
