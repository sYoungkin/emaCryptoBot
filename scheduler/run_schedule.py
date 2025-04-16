# File: schedule/run_scheduler.py
from apscheduler.schedulers.blocking import BlockingScheduler
import subprocess

scheduler = BlockingScheduler()

# 🔧 Customize your parameters here
SYMBOL = "BTC/USDT"
TIMEFRAME = "1m"
CAPITAL = "500"
STOP_LOSS = "0.02"

@scheduler.scheduled_job('interval', minutes=1)
def run_test_bot():
    print("\n⏳ Scheduler triggered...")

    subprocess.run([
        "python", "live/bybit_bot_test.py",
        "--symbol", SYMBOL,
        "--timeframe", TIMEFRAME,
        "--capital", CAPITAL,
        "--stop", STOP_LOSS
    ], check=True)

if __name__ == "__main__":
    print(f"📅 Scheduler started. Running every 1 minute for {SYMBOL} @ {TIMEFRAME}")
    scheduler.start()