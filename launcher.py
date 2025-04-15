# trading-bot: EMA 9/20 Crossover Strategy

# Structure:
# - .env                        => Holds API keys (never commit this!)
# - launcher.py                 => Launch menu for backtest / live bot / scheduler
# - data/fetch_data.py          => Gets historical OHLCV data
# - strategy/ema_crossover.py   => Strategy logic
# - backtest/backtest.py        => Simulates the strategy + visualization + logging
# - live/binance_bot.py         => Live trading via ccxt (with safety + stop-loss)
# - scheduler/run_schedule.py   => Runs bot on cron or ad-hoc

# File: launcher.py
import os
import sys
import warnings
warnings.filterwarnings("ignore")

options = {
    '1': 'Fetch Binance OHLCV data',
    '2': 'Run backtest and plot results',
    '3': 'Run live signal bot (dry run)',
    '4': 'Start scheduler (cron job)',
    '5': 'Exit'
}

def execute_choice(choice):
    if choice == '1':
        os.system("python data/fetch_data.py")
    elif choice == '2':
        os.system("python -m backtest.backtest")
    elif choice == '3':
        os.system("python live/binance_bot.py")
    elif choice == '4':
        os.system("python scheduler/run_schedule.py")
    elif choice == '5':
        print("Goodbye!")
        sys.exit(0)
    else:
        print("Invalid choice. Try again.")


def main():
    if len(sys.argv) > 1:
        # Run the chosen task and exit
        execute_choice(sys.argv[1])
        sys.exit(0)
    else:
        while True:
            print("\nWhat would you like to do?")
            for k, v in options.items():
                print(f"{k}. {v}")
            choice = input("Enter your choice: ").strip()
            execute_choice(choice)
            again = input("\nRun another task? (y/n): ").strip().lower()
            if again != 'y':
                print("Exiting launcher. Bye!")
                break

if __name__ == '__main__':
    main()