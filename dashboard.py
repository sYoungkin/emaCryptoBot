import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from strategy.ema_crossover import ema_crossover_strategy
from backtest.backtest import backtest
import os

st.set_page_config(layout="wide")

st.title("📈 EMA Strategy Dashboard")

with st.sidebar:
    st.header("Strategy Settings")
    pair = st.selectbox("Pair", ["BTCUSDT"], index=0)
    candle_size = st.selectbox("Candle Size", ["1m", "5m", "15m", "1h", "4h"], index=3)
    limit = st.number_input("# of Candles", min_value=100, max_value=10000, value=1000, step=100)

    ema_short = st.slider("EMA Short", 3, 50, 5)
    ema_long = st.slider("EMA Long", 5, 100, 9)
    stop_loss = st.slider("Stop Loss %", 0.0, 0.1, 0.02)
    take_profit = st.slider("Take Profit %", 0.0, 0.2, 0.04)

    run_btn = st.button("🚀 Run Backtest")

if run_btn:
    try:
        filepath = f"data/{pair}_{candle_size}.csv"
        df = pd.read_csv(filepath, index_col="timestamp", parse_dates=True).tail(limit)

        # Patch strategy config dynamically
        from strategy import ema_crossover
        ema_crossover.EMA_SHORT = ema_short
        ema_crossover.EMA_LONG = ema_long
        ema_crossover.STOPLOSS_THRESHOLD = stop_loss
        ema_crossover.TAKEPROFIT_THRESHOLD = take_profit

        df = backtest(df)

        # Load results
        trades = pd.read_csv("logs/trades.csv")

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Return", f"${df['equity_curve'].iloc[-1] - 10000:.2f}")
        col2.metric("Win Rate", f"{(df['strategy_returns'] > 0).mean():.2%}")
        col3.metric("Max Drawdown", f"{(df['equity_curve'] / df['equity_curve'].cummax() - 1).min():.2%}")

        st.subheader("📈 Equity Curve")
        fig1, ax1 = plt.subplots(figsize=(12, 3))
        df['equity_curve'].plot(ax=ax1)
        ax1.set_ylabel("Equity")
        st.pyplot(fig1)

        st.subheader("📊 Trades Table")
        st.dataframe(trades, use_container_width=True)

        st.subheader("📷 Price Chart")
        st.image("logs/backtest_plot.png")

    except FileNotFoundError:
        st.error(f"Data file not found: {filepath}")
    except Exception as e:
        st.exception(e)