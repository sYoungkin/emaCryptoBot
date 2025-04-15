# File: evaluate/strategy_report.py
import csv
import pandas as pd
from strategy.ema_crossover import ema_crossover_strategy
import warnings
warnings.filterwarnings("ignore")

# Extended grid of toggle combinations
configs = [
    {'USE_RSI': False, 'USE_MACD': False, 'USE_RSI_EXIT': False, 'USE_STOPLOSS': False},
    {'USE_RSI': False, 'USE_MACD': False, 'USE_RSI_EXIT': True,  'USE_STOPLOSS': False},
    {'USE_RSI': False, 'USE_MACD': False, 'USE_RSI_EXIT': False, 'USE_STOPLOSS': True},
    {'USE_RSI': False, 'USE_MACD': False, 'USE_RSI_EXIT': True,  'USE_STOPLOSS': True},
    {'USE_RSI': True,  'USE_MACD': False, 'USE_RSI_EXIT': True,  'USE_STOPLOSS': True},
    {'USE_RSI': False, 'USE_MACD': True,  'USE_RSI_EXIT': True,  'USE_STOPLOSS': True},
    {'USE_RSI': True,  'USE_MACD': True,  'USE_RSI_EXIT': True,  'USE_STOPLOSS': True}
]

REPORT_PATH = 'logs/strategy_report.csv'

def run_config_tests():
    df = pd.read_csv("data/BTCUSDT_1h.csv", index_col="timestamp", parse_dates=True)
    results = []

    for cfg in configs:
        import strategy.ema_crossover as strat
        strat.USE_RSI = cfg['USE_RSI']
        strat.USE_MACD = cfg['USE_MACD']
        strat.USE_RSI_EXIT = cfg['USE_RSI_EXIT']
        strat.USE_STOPLOSS = cfg['USE_STOPLOSS']
        strat.USE_VERBOSE = False

        print(f"Testing: RSI={cfg['USE_RSI']} MACD={cfg['USE_MACD']} EXIT_RSI={cfg['USE_RSI_EXIT']} SL={cfg['USE_STOPLOSS']}")

        df_result = ema_crossover_strategy(df.copy())
        df_result['returns'] = df_result['close'].pct_change().fillna(0)
        df_result['strategy_returns'] = df_result['position'] * df_result['returns']
        df_result['equity_curve'] = (1 + df_result['strategy_returns']).cumprod() * 10000

        total_return = df_result['equity_curve'].iloc[-1] - 10000
        win_rate = (df_result['strategy_returns'] > 0).sum() / df_result['strategy_returns'].count()
        max_drawdown = (df_result['equity_curve'] / df_result['equity_curve'].cummax() - 1).min()
        trade_count = df_result['position'].diff().abs().sum() / 2

        results.append({
            'USE_RSI': cfg['USE_RSI'],
            'USE_MACD': cfg['USE_MACD'],
            'USE_RSI_EXIT': cfg['USE_RSI_EXIT'],
            'USE_STOPLOSS': cfg['USE_STOPLOSS'],
            'Total Return': round(total_return, 2),
            'Win Rate': round(win_rate, 4),
            'Max Drawdown': round(max_drawdown, 4),
            'Trades': int(trade_count)
        })

    keys = results[0].keys()
    with open(REPORT_PATH, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)

    print(f"Strategy report saved to {REPORT_PATH}")

if __name__ == "__main__":
    run_config_tests()