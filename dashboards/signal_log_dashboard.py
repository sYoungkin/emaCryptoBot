# File: dashboard/signal_log_dashboard.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from strategy.ema_crossover import ema_crossover_strategy

st.set_page_config(layout="wide")
st.title("📋 Bot Signal Log Viewer")

# Load log file
LOG_PATH = "../logs/test_bot_log.csv"

try:
    log_df = pd.read_csv(LOG_PATH, parse_dates=['timestamp'])
    log_df.set_index("timestamp", inplace=True)

    st.sidebar.header("EMA Settings")
    ema_short = st.sidebar.slider("EMA Short", 3, 50, 5)
    ema_long = st.sidebar.slider("EMA Long", 5, 100, 9)
    use_rsi = st.sidebar.checkbox("Show RSI", value=True)
    use_macd = st.sidebar.checkbox("Show MACD", value=True)

    # Dummy OHLC reconstruction from price column
    df = pd.DataFrame()
    df["close"] = log_df["price"]
    df["open"] = df["close"]
    df["high"] = df["close"]
    df["low"] = df["close"]
    df["volume"] = 1
    df.index = log_df.index

    # Compute indicators from strategy
    indicators_df = ema_crossover_strategy(df.copy(), symbol="BTC/USDT", short_window=ema_short, long_window=ema_long, capital=10000, log_trades=False)

    # Pull just EMA, RSI, MACD over — but do NOT use strategy signals
    df["EMA_SHORT"] = indicators_df["EMA_SHORT"]
    df["EMA_LONG"] = indicators_df["EMA_LONG"]
    df["RSI"] = indicators_df.get("RSI")
    df["MACD"] = indicators_df.get("MACD")
    df["MACD_signal"] = indicators_df.get("MACD_signal")

    # Insert actual signals from log
    df["signal"] = log_df["signal"]

    # === 🧮 Performance Summary ===
    st.subheader("📊 Performance Summary")
    total_signals = log_df[log_df['signal'].isin(['🟢 BUY', '🔴 SELL'])].shape[0]
    buy_signals = log_df[log_df['signal'] == '🟢 BUY'].shape[0]
    sell_signals = log_df[log_df['signal'] == '🔴 SELL'].shape[0]
    avg_position_value = log_df['position_value'].mean()
    avg_stop = (log_df['price'] - log_df['stop_loss']).abs().mean()
    avg_tp = (log_df['take_profit'] - log_df['price']).abs().mean()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Signals", total_signals)
    col2.metric("Buys / Sells", f"{buy_signals} / {sell_signals}")
    col3.metric("Avg Position Size ($)", f"${avg_position_value:.2f}")

    col4, col5 = st.columns(2)
    col4.metric("Avg Stop Distance ($)", f"${avg_stop:.2f}")
    col5.metric("Avg Take Profit Distance ($)", f"${avg_tp:.2f}")

    # === 📈 Price Chart ===
    st.subheader("📈 Price Chart with Signals")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['close'], name="Close", line=dict(color="gray")))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_SHORT'], name=f"EMA {ema_short}", line=dict(color="red")))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_LONG'], name=f"EMA {ema_long}", line=dict(color="blue")))

    buys = df[df['signal'] == '🟢 BUY']
    sells = df[df['signal'] == '🔴 SELL']
    fig.add_trace(go.Scatter(x=buys.index, y=buys['close'], mode='markers', marker_symbol='triangle-up',
                             marker_color='green', marker_size=10, name='BUY'))
    fig.add_trace(go.Scatter(x=sells.index, y=sells['close'], mode='markers', marker_symbol='triangle-down',
                             marker_color='red', marker_size=10, name='SELL'))

    fig.update_layout(height=500, xaxis_title="Time", yaxis_title="Price", hovermode='x unified')
    st.plotly_chart(fig, use_container_width=True)

    # === 📊 Indicators ===
    if use_rsi and 'RSI' in df.columns:
        st.subheader("📉 RSI")
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='purple')))
        fig_rsi.add_hline(y=70, line_dash='dash', line_color='red')
        fig_rsi.add_hline(y=30, line_dash='dash', line_color='green')
        fig_rsi.update_layout(height=250)
        st.plotly_chart(fig_rsi, use_container_width=True)

    if use_macd and 'MACD' in df.columns:
        st.subheader("📉 MACD")
        fig_macd = go.Figure()
        fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD', line=dict(color='blue')))
        fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD_signal'], name='Signal Line', line=dict(color='orange')))
        fig_macd.add_hline(y=0, line_dash='dash', line_color='gray')
        fig_macd.update_layout(height=250)
        st.plotly_chart(fig_macd, use_container_width=True)

    # === 🧠 Strategy Suggestion ===
    st.subheader("📘 Strategy Suggestions")
    latest_signal = df['signal'].iloc[-1]
    if latest_signal == '🟢 BUY':
        st.success("📈 Current signal is BUY → Consider long-biased strategy like EMA crossover.")
    elif latest_signal == '🔴 SELL':
        st.error("📉 Current signal is SELL → Consider short-selling or momentum reversal strategy.")
    else:
        st.warning("🔍 HOLD signal → Wait for breakout confirmation or sideways strategy.")

    # === 📋 Signal Log Table ===
    st.subheader("📝 Signal Log")
    st.dataframe(log_df)

except FileNotFoundError:
    st.error("Log file 'test_bot_log.csv' not found.")
except Exception as e:
    st.exception(e)