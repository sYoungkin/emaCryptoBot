# File: dashboard/market_regime_dashboard.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from data.fetch_data import fetch_bybit_data

st.set_page_config(layout="wide")
st.title("🧠 Market Regime Analyzer")

# Sidebar
st.sidebar.header("Configuration")
symbol = st.sidebar.selectbox("Symbol", ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"], index=0)
timeframe = st.sidebar.selectbox("Timeframe", ["1m", "5m", "15m", "1h", "4h"], index=0)
range_filter = st.sidebar.selectbox("Lookback Period", ["1 Hour", "4 Hours", "1 Day", "1 Week", "1 Month"], index=2)

# Time mapping
now = datetime.utcnow()
range_map = {
    "1 Hour": now - timedelta(hours=1),
    "4 Hours": now - timedelta(hours=4),
    "1 Day": now - timedelta(days=1),
    "1 Week": now - timedelta(weeks=1),
    "1 Month": now - timedelta(days=30),
}

# Dynamic limit calculator
timeframe_minutes = {
    "1m": 1,
    "5m": 5,
    "15m": 15,
    "1h": 60,
    "4h": 240
}
start_time = range_map[range_filter]
minutes_per_candle = timeframe_minutes[timeframe]
minutes_requested = (now - start_time).total_seconds() / 60
limit = int(minutes_requested / minutes_per_candle)
limit = min(limit, 5000)

# Fetch data
df = fetch_bybit_data(symbol, timeframe, limit=limit)
df = df[df.index >= start_time]

# Compute indicators
def compute_indicators(df):
    df['EMA_SHORT'] = df['close'].ewm(span=5, adjust=False).mean()
    df['EMA_LONG'] = df['close'].ewm(span=20, adjust=False).mean()
    df['EMA_Spread'] = df['EMA_SHORT'] - df['EMA_LONG']
    df['ATR'] = df['high'] - df['low']
    df['ATR'] = df['ATR'].rolling(window=14).mean()
    df['Upper_BB'] = df['close'].rolling(20).mean() + 2 * df['close'].rolling(20).std()
    df['Lower_BB'] = df['close'].rolling(20).mean() - 2 * df['close'].rolling(20).std()
    df['BB_Width'] = df['Upper_BB'] - df['Lower_BB']

    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

    up_moves = df['high'] - df['high'].shift(1)
    down_moves = df['low'].shift(1) - df['low']
    plus_dm = np.where((up_moves > down_moves) & (up_moves > 0), up_moves, 0.0)
    minus_dm = np.where((down_moves > up_moves) & (down_moves > 0), down_moves, 0.0)
    tr = df[['high', 'low', 'close']].max(axis=1) - df[['high', 'low', 'close']].min(axis=1)
    tr_smooth = pd.Series(tr).rolling(window=14).mean()
    plus_di = 100 * pd.Series(plus_dm).rolling(window=14).mean() / tr_smooth
    minus_di = 100 * pd.Series(minus_dm).rolling(window=14).mean() / tr_smooth
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    #df['ADX'] = dx.rolling(window=14).mean()

    
    return df

def compute_adx(df, window=14):
    high = df['high']
    low = df['low']
    close = df['close']

    # Calculate directional movement
    plus_dm = high.diff()
    minus_dm = low.diff()

    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0
    minus_dm = minus_dm.abs()

    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    tr_smooth = tr.rolling(window=window).sum()
    plus_di = 100 * plus_dm.rolling(window=window).sum() / tr_smooth
    minus_di = 100 * minus_dm.rolling(window=window).sum() / tr_smooth
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)

    adx = dx.rolling(window=window).mean()
    return adx

df['ADX'] = compute_adx(df)
df = compute_indicators(df)

# Detect regime
def label_regime(row):
    if row['ADX'] > 25 and abs(row['EMA_Spread']) > 0:
        return 'Trending'
    elif row['BB_Width'] > df['BB_Width'].rolling(50).mean().mean():
        return 'Volatile'
    else:
        return 'Choppy'

df['Regime'] = df.apply(label_regime, axis=1)

# Plot price chart
st.subheader("📉 Price with Regime Shading")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['close'], name="Close", line=dict(color='black')))
fig.add_trace(go.Scatter(x=df.index, y=df['EMA_SHORT'], name="EMA 5", line=dict(color='red')))
fig.add_trace(go.Scatter(x=df.index, y=df['EMA_LONG'], name="EMA 20", line=dict(color='blue')))

colors = {'Trending': 'rgba(0,255,0,0.1)', 'Choppy': 'rgba(255,165,0,0.1)', 'Volatile': 'rgba(255,0,0,0.1)'}
last_regime = None
start_idx = None

for i in range(len(df)):
    current_regime = df['Regime'].iloc[i]
    if current_regime != last_regime:
        if start_idx is not None:
            fig.add_vrect(
                x0=df.index[start_idx], x1=df.index[i-1],
                fillcolor=colors.get(last_regime, 'gray'),
                layer="below", line_width=0
            )
        start_idx = i
        last_regime = current_regime
if start_idx is not None:
    fig.add_vrect(
        x0=df.index[start_idx], x1=df.index[-1],
        fillcolor=colors.get(last_regime, 'gray'),
        layer="below", line_width=0
    )

fig.update_layout(height=400, xaxis_title="Time", yaxis_title="Price", hovermode='x unified')
st.plotly_chart(fig, use_container_width=True)
st.caption("Regimes shaded by type: green = trending, orange = choppy, red = volatile.")

# Regime log
st.subheader("📄 Regime Log")
log_df = df[['close', 'RSI', 'ADX', 'ATR', 'BB_Width', 'EMA_Spread', 'Regime']].copy()
log_df = log_df[::-1]  # Most recent first
st.dataframe(
    log_df.style.applymap(
        lambda v: 'background-color: lightgreen' if v == 'Trending' else
                  'background-color: orange' if v == 'Choppy' else
                  'background-color: lightcoral',
        subset=["Regime"]
    ),
    use_container_width=True
)

# Indicator Charts

st.subheader("🔧 ATR (Volatility)")
st.caption("ATR (Average True Range) shows the average volatility range of recent candles. Higher = more volatile.")
fig_atr = go.Figure()
fig_atr.add_trace(go.Scatter(x=df.index, y=df['ATR'], name='ATR', line=dict(color='purple')))
fig_atr.update_layout(height=250, xaxis_title="Time", yaxis_title="ATR")
st.plotly_chart(fig_atr, use_container_width=True)

st.subheader("📏 ADX (Trend Strength)")
st.caption("ADX measures trend strength. Above 25 = strong trend, below = weak or range-bound.")
fig_adx = go.Figure()
fig_adx.add_trace(go.Scatter(x=df.index, y=df['ADX'], name='ADX', line=dict(color='blue')))
fig_adx.add_hline(y=25, line_dash='dash', line_color='gray')
fig_adx.update_layout(height=250)
st.plotly_chart(fig_adx, use_container_width=True)

st.subheader("📉 EMA Spread")
st.caption("EMA Spread shows direction and separation of short/long trends. Used for crossover logic.")
fig_spread = go.Figure()
fig_spread.add_trace(go.Scatter(x=df.index, y=df['EMA_Spread'], name='EMA Spread', line=dict(color='orange')))
fig_spread.update_layout(height=250)
st.plotly_chart(fig_spread, use_container_width=True)

st.subheader("📊 Bollinger Band Width")
st.caption("Bollinger Band Width expands during high volatility. Constriction can precede breakout moves.")
fig_bb = go.Figure()
fig_bb.add_trace(go.Scatter(x=df.index, y=df['BB_Width'], name='BB Width', line=dict(color='green')))
fig_bb.update_layout(height=250)
st.plotly_chart(fig_bb, use_container_width=True)

st.subheader("📈 RSI")
st.caption("RSI shows overbought (>70) or oversold (<30) zones. Useful in choppy or range-bound markets.")
fig_rsi = go.Figure()
fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='purple')))
fig_rsi.add_hline(y=70, line_dash='dash', line_color='red')
fig_rsi.add_hline(y=30, line_dash='dash', line_color='green')
fig_rsi.update_layout(height=250)
st.plotly_chart(fig_rsi, use_container_width=True)