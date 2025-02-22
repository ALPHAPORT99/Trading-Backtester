import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

# Streamlit UI
st.set_page_config(page_title="Trading Strategy Backtester", layout="wide")
st.title("📈 Trading Strategy Backtester")

# Sidebar Inputs
st.sidebar.header("⚙️ Settings")
ticker = st.sidebar.text_input("Enter Stock Ticker (e.g., AAPL, TSLA, BTC-USD)", "AAPL")
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("2024-01-01"))
strategy = st.sidebar.selectbox("Select Strategy", ["Mean Reversion (RSI)", "Momentum (MACD)"])
run_backtest = st.sidebar.button("Run Backtest")

# Fetch Data
if run_backtest:
    with st.spinner("Fetching Data..."):
        try:
            df = yf.download(ticker, start=start_date, end=end_date)
            if df.empty:
                st.error("No data found for the selected ticker and date range.")
                st.stop()
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            st.stop()
    
    # Apply Strategy Logic
    buy_signals, sell_signals = [], []
    capital = 10000  # Starting capital
    position = 0  # No position initially

    for i in range(1, len(df)):
        if strategy == "Mean Reversion (RSI)":
            df['RSI'] = df['Close'].rolling(14).mean()
            if df['RSI'].iloc[i] < 30 and position == 0:  # Buy Signal
                buy_signals.append(df.index[i])
                position = capital / df['Close'].iloc[i]
                capital = 0
            elif df['RSI'].iloc[i] > 70 and position > 0:  # Sell Signal
                sell_signals.append(df.index[i])
                capital = position * df['Close'].iloc[i]
                position = 0
        elif strategy == "Momentum (MACD)":
            df['MACD'] = df['Close'].ewm(span=12, adjust=False).mean() - df['Close'].ewm(span=26, adjust=False).mean()
            df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            if df['MACD'].iloc[i] > df['Signal'].iloc[i] and position == 0:
                buy_signals.append(df.index[i])
                position = capital / df['Close'].iloc[i]
                capital = 0
            elif df['MACD'].iloc[i] < df['Signal'].iloc[i] and position > 0:
                sell_signals.append(df.index[i])
                capital = position * df['Close'].iloc[i]
                position = 0

    # Performance Calculation
    final_value = capital + (position * df['Close'].iloc[-1])
    profit_pct = ((final_value - 10000) / 10000) * 100

    # Metrics Display
    col1, col2 = st.columns(2)
    col1.metric("Final Portfolio Value", f"${final_value:,.2f}")
    col2.metric("Total Return", f"{profit_pct:.2f}%")
    
    # Visualization with Plotly
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name='Close Price', line=dict(color='blue')))
    if buy_signals:
        fig.add_trace(go.Scatter(x=buy_signals, y=df.loc[buy_signals]['Close'], mode='markers', name='Buy Signal', marker=dict(color='green', size=10, symbol='triangle-up')))
    if sell_signals:
        fig.add_trace(go.Scatter(x=sell_signals, y=df.loc[sell_signals]['Close'], mode='markers', name='Sell Signal', marker=dict(color='red', size=10, symbol='triangle-down')))
    fig.update_layout(title=f"{ticker} Price Chart with Trading Signals", xaxis_title="Date", yaxis_title="Price", template="plotly_dark")
    st.plotly_chart(fig)
    
    # Display Performance Metrics
    st.subheader("📊 Backtest Results")
    st.write(f"Final Portfolio Value: ${final_value:,.2f}")
    st.write(f"Total Return: {profit_pct:.2f}%")
    
    # Download Results
    csv = df.to_csv(index=False)
    st.download_button("Download Results as CSV", csv, file_name="backtest_results.csv", mime="text/csv")
