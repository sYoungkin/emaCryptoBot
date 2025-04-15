# EMA Crypto Bot - Strategy Backtesting & Live Trading

This project combines an interactive dashboard for strategy development with a real-time trading bot for live execution on Binance using EMA crossover logic.

---

## 🚀 Features

### 🧪 Backtesting via Dashboard (Streamlit)
- Interactive EMA strategy explorer
- Compare multiple EMA pairs with win rate, drawdown, and return
- RSI, MACD, VWAP indicators (always visible)
- Backtest results: trade markers, equity curve, metrics
- Chart types: Line / Candlestick
- Adjustable:
  - Pair, Candle Size, Data Limit
  - EMA short/long
  - Stop Loss / Take Profit
  - Leverage
  - Initial capital

### 🤖 Live Trading Bot (Binance)
- Uses same EMA strategy logic as dashboard
- Paper mode and live trading mode
- Binance integration via `ccxt`
- Trade sizing based on 2% risk per trade
- Telegram alert integration (or WhatsApp via Twilio)
- Scheduled execution via `APScheduler`
- Trade log to `logs/live_trades.csv`
- OCO logic (stop loss + take profit) implemented for future use

---

## 📦 Project Structure

```
.
├── dashboard.py              # Streamlit dashboard
├── live/
│   └── binance_bot.py        # Live trading bot
├── strategy/
│   └── ema_crossover.py      # EMA crossover strategy logic
├── data/
│   └── fetch_data.py         # Fetch OHLCV from Binance
├── backtest/
│   └── backtest.py           # Backtest engine + plot
├── schedule/
│   └── run_schedule.py       # APScheduler for bot
├── logs/                     # Trade logs and backtest plots
├── .env                      # API keys and secrets
└── requirements.txt          # Python dependencies
```

---

## ⚙️ Getting Started

### 1. Clone & Set Up
```bash
git clone https://github.com/your-repo/ema-crypto-bot.git
cd ema-crypto-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure `.env`
Create a `.env` file in the root:
```
BINANCE_API_KEY=your_api_key
BINANCE_SECRET=your_api_secret
TELEGRAM_TOKEN=your_telegram_token
TELEGRAM_CHAT_ID=your_chat_id
```

To use WhatsApp via Twilio instead, configure:
```
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
TWILIO_WHATSAPP_TO=whatsapp:+4915123456789
```

---

## 📊 Run Dashboard
```bash
streamlit run dashboard.py
```

Use this to:
- Explore pairs and EMA configs
- Visualize trade logic
- Optimize strategy before going live

---

## 🤖 Run the Live Trading Bot
### Paper Mode:
```bash
python live/binance_bot.py --symbol BTC/USDT --timeframe 1m --capital 500 --stop 0.02 --mode paper
```

### Live Mode:
```bash
python live/binance_bot.py --symbol BTC/USDT --timeframe 1m --mode live
```
Ensure you have sufficient balance in your Binance account.

---

## ⏱️ Schedule the Bot
```bash
python schedule/run_schedule.py
```
Edit the schedule in `run_schedule.py` to run hourly, daily, or custom.

---

## 📄 Logs
- All executed trades (paper or live) are logged to:
  ```
  logs/live_trades.csv
  ```
- Backtest charts saved to:
  ```
  logs/backtest_plot.png
  ```

---

## 🛠️ To-Do / Roadmap
- Trailing stop logic
- Portfolio optimization across assets
- Auto-preset selection based on recent performance
- Real account performance dashboard

---

## 💬 Telegram Bot Setup
1. Create bot via [@BotFather](https://t.me/BotFather)
2. Get bot token
3. Start a chat with the bot
4. Get your chat ID via `getUpdates` API or `@userinfobot`
5. Add both to `.env`

---

## 🟢 WhatsApp Notifications (Optional)
1. Create a [Twilio account](https://www.twilio.com/whatsapp)
2. Verify your WhatsApp number
3. Use Twilio's sandbox number and message template

---

## 👨‍💻 Author
Custom developed with ❤️ for interactive, automated trading workflows.
