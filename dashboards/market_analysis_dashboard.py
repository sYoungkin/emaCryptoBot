# File: dashboard/market_regime_dashboard.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data.fetch_data import fetch_bybit_data
from strategy.ema_crossover import compute_rsi, compute_macd, compute_vwap
from datetime import datetime, timedelta

st.set_page_config(layout="wide")
st.title("🧠 Market Regime Analyzer")

# Sidebar controls
st.sidebar.header("Market Settings")
symbol = st.sidebar.selectbox("Symbol", ["BTCUSDT", "ETHUSDT", "BNBUSDT"], index=0)
timeframe = st.sidebar.selectbox("Timeframe", ["1m", "5m", "15m", "1h", "4h"], index=3)
lookback_option = st.sidebar.selectbox("Lookback Range", ["1 Hour", "4 Hours", "1 Day", "3 Days", "1 Week"], index=2)

lookback_map = {
    "1 Hour": timedelta(hours=1),
    "4 Hours": timedelta(hours=4),
    "1 Day": timedelta(days=1),
    "3 Days": timedelta(days=3),
    "1 Week": timedelta(weeks=1)
}

# Fetch and preprocess data
df = fetch_bybit_data(symbol, timeframe, limit=1000)
df['RSI'] = compute_rsi(df['close'])
df['MACD'], df['MACD_signal'] = compute_macd(df['close'])
df['VWAP'] = compute_vwap(df)

# Filter by time
cutoff = df.index.max() - lookback_map[lookback_option]
df = df[df.index >= cutoff]

# Regime detection logic
def detect_regime(row):
    if row['RSI'] > 70 and row['MACD'] > row['MACD_signal']:
        return "Trending"
    elif row['RSI'] < 30 and row['MACD'] < row['MACD_signal']:
        return "Reversal"
    elif abs(row['RSI'] - 50) < 5:
        return "Consolidating"
    else:
        return "Ranging"

df['Regime'] = df.apply(detect_regime, axis=1)

# Strategy Suggestions
def get_strategy(regime):
    if regime == "Trending":
        return "📈 Momentum strategies (e.g., EMA crossover, breakout)"
    elif regime == "Ranging":
        return "🔁 Mean reversion (e.g., Bollinger Band fades, RSI swings)"
    elif regime == "Consolidating":
        return "⏸ Avoid trading or wait for breakout confirmation"
    elif regime == "Reversal":
        return "🔄 Reversal trades (e.g., RSI oversold/bought, MACD cross)"
    else:
        return "🤷 Unknown"

df['Strategy'] = df['Regime'].apply(get_strategy)

# Plotting
st.subheader("📊 Price + VWAP + EMAs")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['close'], name="Close", line=dict(color='gray')))
fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'], name="VWAP", line=dict(color='orange', dash='dash')))
fig.add_trace(go.Scatter(x=df.index, y=df['close'].ewm(span=5).mean(), name="EMA 5", line=dict(color='red')))
fig.add_trace(go.Scatter(x=df.index, y=df['close'].ewm(span=9).mean(), name="EMA 9", line=dict(color='blue')))
fig.update_layout(height=400, xaxis_title="Time", yaxis_title="Price")
st.plotly_chart(fig, use_container_width=True)

st.subheader("📉 RSI")
fig_rsi = go.Figure()
fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='purple')))
fig_rsi.add_hline(y=70, line_dash='dash', line_color='red')
fig_rsi.add_hline(y=30, line_dash='dash', line_color='green')
fig_rsi.update_layout(height=250)
st.caption("RSI shows potential overbought (>70) or oversold (<30) conditions that may indicate reversals.")
st.plotly_chart(fig_rsi, use_container_width=True)

st.subheader("📈 MACD")
fig_macd = go.Figure()
fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD', line=dict(color='blue')))
fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD_signal'], name='Signal Line', line=dict(color='orange')))
fig_macd.add_hline(y=0, line_dash='dash', line_color='gray')
fig_macd.update_layout(height=250)
st.caption("MACD shows trend momentum. Cross above signal line = bullish, below = bearish.")
st.plotly_chart(fig_macd, use_container_width=True)

# Color-coded regime table
st.subheader("🧠 Regime Detection Log")
st.caption("This table shows the detected market regime at each candle and the recommended strategy.")
def color_regimes(val):
    colors = {
        "Trending": "background-color: lightgreen",
        "Ranging": "background-color: khaki",
        "Consolidating": "background-color: lightblue",
        "Reversal": "background-color: salmon"
    }
    return colors.get(val, '')

styled_df = df[['Regime', 'Strategy']].sort_index(ascending=False).style.applymap(color_regimes, subset=['Regime'])
st.dataframe(styled_df, use_container_width=True)