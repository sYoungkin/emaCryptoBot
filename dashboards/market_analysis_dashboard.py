# File: dashboards/market_regime_dashboard.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data.fetch_data import fetch_bybit_data
import numpy as np

st.set_page_config(layout="wide")
st.title("🧠 Market Regime Analyzer")

st.sidebar.header("Settings")
symbol = st.sidebar.text_input("Symbol (e.g. BTCUSDT)", value="BTCUSDT")
timeframe = st.sidebar.selectbox("Timeframe", ["1m", "5m", "15m", "1h", "4h", "1d"], index=3)
limit = st.sidebar.slider("Lookback Candles", 100, 1000, 500)

try:
    df = fetch_bybit_data(symbol, timeframe, limit)
    df['returns'] = df['close'].pct_change()
    df['EMA_SHORT'] = df['close'].ewm(span=5).mean()
    df['EMA_LONG'] = df['close'].ewm(span=20).mean()

    # ATR - Average True Range
    df['H-L'] = df['high'] - df['low']
    df['H-PC'] = abs(df['high'] - df['close'].shift(1))
    df['L-PC'] = abs(df['low'] - df['close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    df['ATR'] = df['TR'].rolling(window=14).mean()

    # ADX
    df['+DM'] = np.where((df['high'] - df['high'].shift(1)) > (df['low'].shift(1) - df['low']), df['high'] - df['high'].shift(1), 0)
    df['-DM'] = np.where((df['low'].shift(1) - df['low']) > (df['high'] - df['high'].shift(1)), df['low'].shift(1) - df['low'], 0)
    df['+DI'] = 100 * (df['+DM'].ewm(alpha=1/14).mean() / df['ATR'])
    df['-DI'] = 100 * (df['-DM'].ewm(alpha=1/14).mean() / df['ATR'])
    df['DX'] = 100 * abs(df['+DI'] - df['-DI']) / (df['+DI'] + df['-DI'])
    df['ADX'] = df['DX'].ewm(alpha=1/14).mean()

    # Bollinger Band Width
    df['MA20'] = df['close'].rolling(window=20).mean()
    df['STD20'] = df['close'].rolling(window=20).std()
    df['BB_width'] = df['STD20'] * 4 / df['MA20']

    # RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # Determine regime
    def determine_regime(row):
        if row['ADX'] > 25 and abs(row['EMA_SHORT'] - row['EMA_LONG']) / row['close'] > 0.01:
            return "Trending"
        elif row['BB_width'] < 0.02 and 40 < row['RSI'] < 60:
            return "Consolidating"
        elif row['RSI'] > 70 or row['RSI'] < 30:
            return "Reversal Possible"
        else:
            return "Ranging"

    df['Regime'] = df.apply(determine_regime, axis=1)
    latest = df.iloc[-1]

    st.header(f"📊 Latest Regime: {latest['Regime']}")

    suggestion = {
        "Trending": "Use trend-following strategies: EMA crossover, breakout systems, trailing stops.",
        "Ranging": "Use mean-reversion systems: Bollinger bounce, RSI oversold/overbought fades.",
        "Consolidating": "Reduce trading. Wait for volatility breakout or news-driven move.",
        "Reversal Possible": "Use reversal signals: divergence setups, candle patterns, contrarian trades."
    }
    st.info(suggestion[latest['Regime']])

    st.subheader("📈 Price Chart with Regime")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['close'], name='Close'))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_SHORT'], name='EMA 5'))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_LONG'], name='EMA 20'))
    fig.update_layout(title="Price & EMA", xaxis_title="Time", yaxis_title="Price", height=400)
    st.caption("Short/long EMAs help identify momentum and trend bias. Widening spread indicates stronger direction.")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📉 ADX (Trend Strength)")
    fig_adx = go.Figure()
    fig_adx.add_trace(go.Scatter(x=df.index, y=df['ADX'], name="ADX", line=dict(color='orange')))
    fig_adx.update_layout(title="ADX - Trend Strength", height=300)
    st.caption("ADX above 25 typically signals strong trending conditions. Below 20-25 = range-bound.")
    st.plotly_chart(fig_adx, use_container_width=True)

    st.subheader("📏 Bollinger Band Width")
    fig_bb = go.Figure()
    fig_bb.add_trace(go.Scatter(x=df.index, y=df['BB_width'], name="BB Width"))
    fig_bb.update_layout(title="Bollinger Band Width", height=300)
    st.caption("Low BB width suggests low volatility. Often precedes strong directional move (breakout).")
    st.plotly_chart(fig_bb, use_container_width=True)

    st.subheader("📊 RSI")
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='purple')))
    fig_rsi.update_layout(title="Relative Strength Index", height=300)
    fig_rsi.add_hline(y=70, line_dash='dash', line_color='red')
    fig_rsi.add_hline(y=30, line_dash='dash', line_color='green')
    st.caption("RSI > 70 = overbought, RSI < 30 = oversold. Often used to time entries or spot reversals.")
    st.plotly_chart(fig_rsi, use_container_width=True)

    st.subheader("📋 Full Regime Log")
    st.dataframe(df[['close', 'EMA_SHORT', 'EMA_LONG', 'ATR', 'ADX', 'BB_width', 'RSI', 'Regime']].tail(100), use_container_width=True)

except Exception as e:
    st.error(f"Failed to load data or compute regime: {e}")