from apscheduler.schedulers.blocking import BlockingScheduler
from live.binance_bot import run_live_bot

scheduler = BlockingScheduler()

# Modify this to change timing (e.g., every hour, or custom cron)
@scheduler.scheduled_job('cron', minute='0', hour='*/1')  # every hour
# @scheduler.scheduled_job('interval', minutes=30)  # every 30 minutes
# @scheduler.scheduled_job('cron', minute='15', hour='9-17', day_of_week='mon-fri')  # market hours

def scheduled_job():
    print("Running scheduled trading bot...")
    run_live_bot()

if __name__ == "__main__":
    scheduler.start()