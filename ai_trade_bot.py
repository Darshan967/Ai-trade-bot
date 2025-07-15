import streamlit as st
import pandas as pd
import requests
import datetime
import ta

CRYPTO_SYMBOL = "BTCUSDT"
FOREX_PAIR = "EUR/USD"

def fetch_crypto_data(symbol="BTCUSDT", interval="1h", limit=100):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url)
    data = response.json()

    if not data or not isinstance(data, list):
        raise ValueError("Invalid data received from Binance API")

    try:
        df = pd.DataFrame(data)
        df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume',
                      'close_time', 'quote_asset_volume', 'number_of_trades',
                      'taker_buy_base', 'taker_buy_quote', 'ignore']
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
        return df
    except Exception as e:
        raise ValueError(f"Error processing crypto data: {e}")

def fetch_forex_data(pair="EUR/USD"):
    from forex_python.converter import CurrencyRates
    c = CurrencyRates()
    rate = c.get_rate(pair.split("/")[0], pair.split("/")[1])
    now = datetime.datetime.now()
    df = pd.DataFrame({"rate": [rate]}, index=[now])
    return df

def apply_strategy(df, strategy):
    if strategy == "RSI":
        rsi = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
        last_rsi = rsi.iloc[-1]
        if last_rsi < 30:
            return "Buy (RSI Oversold)", round(last_rsi, 2)
        elif last_rsi > 70:
            return "Sell (RSI Overbought)", round(last_rsi, 2)
        else:
            return "Hold", round(last_rsi, 2)

    elif strategy == "MACD":
        macd = ta.trend.MACD(df['close'])
        macd_line = macd.macd()
        signal_line = macd.macd_signal()
        if macd_line.iloc[-1] > signal_line.iloc[-1]:
            return "Buy (MACD Bullish)", round(macd_line.iloc[-1], 4)
        else:
            return "Sell (MACD Bearish)", round(macd_line.iloc[-1], 4)

    elif strategy == "EMA Crossover":
        ema_fast = df['close'].ewm(span=9, adjust=False).mean()
        ema_slow = df['close'].ewm(span=21, adjust=False).mean()
        if ema_fast.iloc[-1] > ema_slow.iloc[-1]:
            return "Buy (EMA Bullish)", None
        else:
            return "Sell (EMA Bearish)", None

    else:
        return "Strategy not implemented yet", None

st.title("🤖 AI Trade Signal Bot")
market = st.selectbox("Select Market", ["Crypto", "Forex"])
strategy = st.selectbox("Select Strategy", ["RSI", "MACD", "EMA Crossover"])

if st.button("🔍 Get Trade Suggestion"):
    with st.spinner("Fetching market data and analyzing..."):
        try:
            if market == "Crypto":
                df = fetch_crypto_data(CRYPTO_SYMBOL)
                signal, value = apply_strategy(df, strategy)
                if value is not None:
                    st.success(f"{signal} | Indicator Value: {value}")
                else:
                    st.success(f"{signal}")
            elif market == "Forex":
                df = fetch_forex_data(FOREX_PAIR)
                st.success(f"Forex Rate: {df['rate'].iloc[0]}")
                st.info("More technicals coming soon for Forex")
        except Exception as e:
            st.error(f"Error: {e}")

st.caption("Made by ChatGPT for Darshan Patel 🚀")
