import pandas as pd

def ema_crossover_strategy(df, short_window=9, long_window=20):
    df['EMA9'] = df['close'].ewm(span=short_window, adjust=False).mean()
    df['EMA20'] = df['close'].ewm(span=long_window, adjust=False).mean()

    df['signal'] = 0
    df.loc[df['EMA9'] > df['EMA20'], 'signal'] = 1  # Buy
    df.loc[df['EMA9'] < df['EMA20'], 'signal'] = -1 # Sell

    df['position'] = df['signal'].shift(1).fillna(0)  # Avoid lookahead bias
    return df