import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

# Streamlit must be set first
st.set_page_config(page_title="Trading Strategy Backtester", layout="wide")

# Try importing pandas_ta (TA-Lib alternative)
try:
    import pandas_ta as talib
except ImportError:
    st.warning("⚠️ `pandas_ta` is missing! Please check `requirements.txt` and install it.")

st.title("📈 Trading Strategy Backtester")

# Sidebar Inputs
st.sidebar.header("⚙️ Settings")
ticker = st.sidebar.text_input("Enter Stock Ticker (e.g., AAPL, TSLA, BTC-USD)", "AAPL")
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("2024-01-01"))
strategy = st.sidebar.selectbox("Select Strategy", [
    "Simple Moving Average Crossover", "Bollinger Bands", "MACD", "RSI", "Stochastic Oscillator", 
    "Donchian Channel", "Ichimoku Cloud", "Parabolic SAR", "ADX", "Williams %R", 
    "Momentum Indicator", "CCI", "ATR", "Hull Moving Average", "Keltner Channel", 
    "Triple Moving Average Crossover", "Volume Weighted Average Price (VWAP)", "Rate of Change (ROC)", 
    "Elder Ray Index", "Mass Index", "Chande Momentum Oscillator (CMO)", "Guppy Multiple Moving Averages (GMMA)", 
    "Ultimate Oscillator", "Force Index", "Ease of Movement (EOM)", "Chaikin Money Flow (CMF)"
])
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
    
    if strategy == "Simple Moving Average Crossover":
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        for i in range(1, len(df)):
            if df['SMA_50'].iloc[i] > df['SMA_200'].iloc[i] and df['SMA_50'].iloc[i - 1] <= df['SMA_200'].iloc[i - 1]:
                buy_signals.append(df.index[i])
            elif df['SMA_50'].iloc[i] < df['SMA_200'].iloc[i] and df['SMA_50'].iloc[i - 1] >= df['SMA_200'].iloc[i - 1]:
                sell_signals.append(df.index[i])
    
    elif strategy == "RSI":
        df['RSI'] = 100 - (100 / (1 + df['Close'].pct_change().rolling(window=14).mean() / df['Close'].pct_change().rolling(window=14).std()))
        for i in range(1, len(df)):
            if df['RSI'].iloc[i] < 30:
                buy_signals.append(df.index[i])
            elif df['RSI'].iloc[i] > 70:
                sell_signals.append(df.index[i])
    
    elif strategy == "MACD":
        df['MACD'] = df['Close'].ewm(span=12, adjust=False).mean() - df['Close'].ewm(span=26, adjust=False).mean()
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        for i in range(1, len(df)):
            if df['MACD'].iloc[i] > df['Signal'].iloc[i] and df['MACD'].iloc[i - 1] <= df['Signal'].iloc[i - 1]:
                buy_signals.append(df.index[i])
            elif df['MACD'].iloc[i] < df['Signal'].iloc[i] and df['MACD'].iloc[i - 1] >= df['Signal'].iloc[i - 1]:
                sell_signals.append(df.index[i])
    
    # Ensure final_value calculation is numeric
    final_value = capital + (position * df['Close'].iloc[-1]) if not df.empty else capital
    profit_pct = ((final_value - 10000) / 10000) * 100

    # Metrics Display
    col1, col2 = st.columns(2)
    col1.metric("Final Portfolio Value", f"${final_value.iloc[-1]:,.2f}")
    col2.metric("Total Return", f"{profit_pct.iloc[-1]:.2f}%")
    
    # Visualization with Plotly
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name="Close Price", line=dict(color='blue')))
    if buy_signals:
        fig.add_trace(go.Scatter(x=buy_signals, y=df.loc[buy_signals]['Close'], mode='markers', name="Buy Signal", marker=dict(color='green', size=10, symbol='triangle-up')))
    if sell_signals:
        fig.add_trace(go.Scatter(x=sell_signals, y=df.loc[sell_signals]['Close'], mode='markers', name="Sell Signal", marker=dict(color='red', size=10, symbol='triangle-down')))
    fig.update_layout(title=f"{ticker} Price Chart with Trading Signals", xaxis_title="Date", yaxis_title="Price", template="plotly_dark")
    st.plotly_chart(fig)
    
    # Display Performance Metrics
    st.subheader("📊 Backtest Results")
    st.write(f"Final Portfolio Value: ${final_value:,.2f}")
    st.write(f"Total Return: {profit_pct:.2f}%")
    
    # Download Results
    csv = df.to_csv(index=False)
    st.download_button("Download Results as CSV", csv, file_name="backtest_results.csv", mime="text/csv")
