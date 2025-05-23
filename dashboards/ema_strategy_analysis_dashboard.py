import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from strategy import ema_crossover
from backtest.backtest_engine import backtest
from data.fetch_data import save_to_csv
from datetime import datetime


st.set_page_config(layout="wide")

st.title("\U0001F4C8 EMA Strategy Dashboard")

with st.sidebar:
    st.header("Strategy Settings")

    pair = st.selectbox("Pair", ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"], index=0)
    all_timeframes = ["1m", "5m", "15m", "1h", "4h"]
    candle_size = st.selectbox("Candle Size", all_timeframes, index=3)
    limit = st.text_input("# of Candles (e.g. 1000, 5000, 10000)", value="1000")

    st.subheader("EMA Presets")
    ema_presets = {
        "EMA 5/9": (5, 9),
        "EMA 9/20": (9, 20),
        "EMA 10/50": (10, 50),
        "EMA 12/26": (12, 26),
        "EMA 20/50": (20, 50)
    }
    selected_preset = st.selectbox("Choose a preset or set manually:", list(ema_presets.keys()), index=1)
    preset_short, preset_long = ema_presets[selected_preset]

    ema_short = st.slider("EMA Short", 3, 50, preset_short)
    ema_long = st.slider("EMA Long", 5, 100, preset_long)
    initial_balance = st.number_input("Initial Capital ($)", min_value=100, max_value=1_000_000, value=10000, step=100, key="initial_balance_input")
    leverage = st.slider("Leverage", 1, 20, 1, key="leverage_slider")
    stop_loss = st.slider("Stop Loss %", 0.0, 0.1, 0.02, key="stop_loss_slider")
    take_profit = st.slider("Take Profit %", 0.0, 0.2, 0.04, key="take_profit_slider")
    chart_type = st.radio("Price Chart Type", ["Line", "Candlestick"], index=0)

    run_btn = st.button("\U0001F680 Run Backtest")
    compare_btn = st.button("\U0001F4C8 Compare All Presets")

if run_btn or compare_btn:
    try:
        filename = f"{pair}_{candle_size}.csv"
        filepath = f"data/{filename}"
        save_to_csv(pair=pair, timeframe=candle_size, limit=int(limit))
        results = []

        if compare_btn:
            st.subheader(f"\U0001F4CA EMA Preset Comparison for {pair} on {candle_size} candles")
            st.caption("Compares total return, win rate, drawdown, and trade frequency for multiple EMA crossover configurations. Helps identify which preset is most effective for the selected pair and timeframe.")

            for name, (short, long) in ema_presets.items():
                ema_crossover.EMA_SHORT = short
                ema_crossover.EMA_LONG = long
                ema_crossover.STOPLOSS_THRESHOLD = stop_loss
                ema_crossover.TAKEPROFIT_THRESHOLD = take_profit

                df = pd.read_csv(filepath, index_col="timestamp", parse_dates=True)
                df, total_return, win_rate, max_dd = backtest(df, symbol=pair.replace("USDT", "/USDT"), short_window=short, long_window=long, initial_balance=initial_balance, leverage=leverage)
                trade_count = df['position'].diff().abs().sum() / 2
                avg_profit = total_return / trade_count if trade_count else 0

                results.append([name, round(total_return, 2), round(win_rate * 100, 2), round(max_dd * 100, 2), round(trade_count), round(avg_profit, 2)])

            df_results = pd.DataFrame(results, columns=['Preset', 'Return ($)', 'Win Rate (%)', 'Drawdown (%)', 'Trades', 'Profit/Trade ($)'])
            best = df_results.sort_values(by='Return ($)', ascending=False).iloc[0]

            st.dataframe(df_results, use_container_width=True)
            st.success(f"\U0001F3C6 Best preset: {best['Preset']} with ${best['Return ($)']} return")

            st.caption("\U0001F4CA Bar Chart: Compares the total return of each EMA preset. Color intensity reflects the win rate.")
            fig_bar = px.bar(df_results, x='Preset', y='Return ($)', color='Win Rate (%)', title="Total Return by EMA Preset")
            st.plotly_chart(fig_bar, use_container_width=True)

            st.caption("\U0001F7E2 Scatter Plot: Shows trade-off between win rate and return. Larger bubbles = more trades. Lower drawdown is better.")
            fig_scatter = px.scatter(df_results, x='Win Rate (%)', y='Return ($)', text='Preset', size='Trades', color='Drawdown (%)', title="Win Rate vs Return by Preset", hover_name='Preset')
            fig_scatter.update_traces(textposition='top center')
            st.plotly_chart(fig_scatter, use_container_width=True)

        elif run_btn:
            st.subheader(f"\U0001F4C9 Backtest Result for {pair} on {candle_size}")
            st.caption("Price chart with EMA crossovers and VWAP. Entry/exit markers are plotted. RSI and MACD show overbought/oversold zones.")

            ema_crossover.EMA_SHORT = ema_short
            ema_crossover.EMA_LONG = ema_long
            ema_crossover.STOPLOSS_THRESHOLD = stop_loss
            ema_crossover.TAKEPROFIT_THRESHOLD = take_profit

            df = pd.read_csv(filepath, index_col="timestamp", parse_dates=True)
            df['VWAP'] = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
            df, total_return, win_rate, max_dd = backtest(df, symbol=pair.replace("USDT", "/USDT"), short_window=ema_short, long_window=ema_long, initial_balance=initial_balance, leverage=leverage)
            trades_df = pd.read_csv("logs/trades.csv")

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Return", f"${total_return:.2f}")
            col2.metric("Win Rate", f"{win_rate:.2%}")
            col3.metric("Max Drawdown", f"{max_dd:.2%}")

            st.subheader("\U0001F4C8 Price Chart")
            st.caption("Shows price with EMA overlays and VWAP. Entry (green ▲) and exit (red ▼) markers indicate trades.")

            fig_price = go.Figure()
            if chart_type == "Candlestick":
                fig_price.add_trace(go.Candlestick(x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="Candlestick"))
            else:
                fig_price.add_trace(go.Scatter(x=df.index, y=df['close'], name='Close', line=dict(color='gray')))

            fig_price.add_trace(go.Scatter(x=df.index, y=df['EMA_SHORT'], name=f'EMA {ema_short}', line=dict(color='red')))
            fig_price.add_trace(go.Scatter(x=df.index, y=df['EMA_LONG'], name=f'EMA {ema_long}', line=dict(color='blue')))
            fig_price.add_trace(go.Scatter(x=df.index, y=df['VWAP'], name='VWAP', line=dict(color='orange', dash='dash')))

            entries = df[df['signal'] == 1]
            exits = df[df['signal'] == -1]
            fig_price.add_trace(go.Scatter(x=entries.index, y=entries['close'], mode='markers', marker_symbol='triangle-up', marker_color='green', marker_size=10, name='Entry'))
            fig_price.add_trace(go.Scatter(x=exits.index, y=exits['close'], mode='markers', marker_symbol='triangle-down', marker_color='red', marker_size=10, name='Exit'))

            fig_price.update_layout(height=500, hovermode='x unified', xaxis_title="Time", yaxis_title="Price")
            st.plotly_chart(fig_price, use_container_width=True)

            st.subheader("\U0001F7E3 RSI")
            st.caption("RSI (Relative Strength Index) helps identify overbought (>70) and oversold (<30) conditions.")
            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], mode='lines', name='RSI', line=dict(color='purple')))
            fig_rsi.add_hline(y=70, line_dash='dash', line_color='red')
            fig_rsi.add_hline(y=30, line_dash='dash', line_color='green')
            fig_rsi.update_layout(height=300, hovermode='x unified', xaxis_title="Time", yaxis_title="RSI")
            st.plotly_chart(fig_rsi, use_container_width=True)

            st.subheader("\U0001F535 MACD")
            st.caption("MACD shows trend momentum via short/long EMA crossovers. Cross above signal = bullish.")
            fig_macd = go.Figure()
            fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD', line=dict(color='blue')))
            fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD_signal'], name='Signal Line', line=dict(color='orange')))
            fig_macd.add_hline(y=0, line_dash='dash', line_color='gray')
            fig_macd.update_layout(height=300, hovermode='x unified', xaxis_title="Time", yaxis_title="MACD")
            st.plotly_chart(fig_macd, use_container_width=True)

            if 'volume' in df.columns:
                st.subheader("\U0001F4CA Volume")
                st.caption("Shows trading volume per candle. Helps identify strong price moves with volume confirmation.")
                fig_vol = go.Figure()
                fig_vol.add_trace(go.Bar(x=df.index, y=df['volume'], name='Volume', marker_color='lightblue'))
                fig_vol.update_layout(height=250, xaxis_title="Time", yaxis_title="Volume", hovermode='x unified')
                st.plotly_chart(fig_vol, use_container_width=True)

            st.subheader("\U0001F4CB Trades Log")
            st.dataframe(trades_df, use_container_width=True)

    except FileNotFoundError:
        st.error(f"Data file not found or failed to fetch: {filepath}")
    except Exception as e:
        st.exception(e)