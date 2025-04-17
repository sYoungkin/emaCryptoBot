# File: dashboards/compare_logs_dashboard.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from strategy.ema_crossover import compute_rsi, compute_macd

st.set_page_config(layout="wide")
st.title("📊 Compare Bot Logs (Stateful vs Stateless)")

# === Paths ===
STATELESS_PATH = "logs/test_bot_log"
STATEFUL_PATH = "logs/test_bot_log_stateful"

# === Detect Dates ===
def list_log_dates(path):
    return sorted([
        f.replace(".csv", "")
        for f in os.listdir(path)
        if f.endswith(".csv")
    ])

dates_stateless = list_log_dates(STATELESS_PATH)
dates_stateful = list_log_dates(STATEFUL_PATH)
all_dates = sorted(set(dates_stateless + dates_stateful))

today = datetime.utcnow().strftime("%Y-%m-%d")
default_index = all_dates.index(today) if today in all_dates else len(all_dates) - 1

selected_date = st.sidebar.selectbox("Select Date", all_dates, index=default_index)

# === Load Logs ===
def load_log(path, date):
    try:
        df = pd.read_csv(os.path.join(path, f"{date}.csv"), parse_dates=['timestamp'])
        df.set_index('timestamp', inplace=True)
        return df
    except FileNotFoundError:
        return pd.DataFrame()

df_stateless = load_log(STATELESS_PATH, selected_date)
df_stateful = load_log(STATEFUL_PATH, selected_date)

def enrich_df(df):
    if df.empty:
        return df
    df['EMA_5'] = df['price'].ewm(span=5, adjust=False).mean()
    df['EMA_9'] = df['price'].ewm(span=9, adjust=False).mean()
    df['RSI'] = compute_rsi(df['price'])
    df['MACD'], df['MACD_signal'] = compute_macd(df['price'])
    return df

df_stateless = enrich_df(df_stateless)
df_stateful = enrich_df(df_stateful)

# === Chart Function ===
def plot_signals(df, title):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['price'], name="Price", line=dict(color='gray')))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_5'], name="EMA 5", line=dict(color='red')))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_9'], name="EMA 9", line=dict(color='blue')))
    
    buys = df[df['signal'] == '🟢 BUY']
    sells = df[df['signal'] == '🔴 SELL']
    fig.add_trace(go.Scatter(x=buys.index, y=buys['price'], mode='markers', name="BUY", marker=dict(symbol='triangle-up', color='green', size=10)))
    fig.add_trace(go.Scatter(x=sells.index, y=sells['price'], mode='markers', name="SELL", marker=dict(symbol='triangle-down', color='red', size=10)))

    fig.update_layout(title=title, height=500, xaxis_title="Time", yaxis_title="Price", hovermode="x unified")
    return fig

# === Display Charts ===
col1, col2 = st.columns(2)

with col1:
    st.subheader("🧠 Stateful Bot")
    if not df_stateful.empty:
        st.plotly_chart(plot_signals(df_stateful, "Stateful Bot Signals"), use_container_width=True)
    else:
        st.warning("No stateful log found for this date.")

with col2:
    st.subheader("⚙️ Stateless Bot")
    if not df_stateless.empty:
        st.plotly_chart(plot_signals(df_stateless, "Stateless Bot Signals"), use_container_width=True)
    else:
        st.warning("No stateless log found for this date.")