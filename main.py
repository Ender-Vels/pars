import streamlit as st
import requests
import time
import hmac
import hashlib

# Function to fetch trade data from Binance API
def fetch_trade_data(api_endpoint, trader_id):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }
    params = {
        'traderId': trader_id,
        'limit': 1000
    }
    response = requests.get(api_endpoint, headers=headers, params=params)
    trades = response.json()['data']
    return trades

# Function to summarize trades within a 2-second interval
def summarize_trades(trades):
    summarized_trades = []
    for i in range(len(trades) - 1):
        current_trade = trades[i]
        next_trade = trades[i + 1]
        if (next_trade['time'] - current_trade['time']) <= 2000:
            current_trade['quantity'] += next_trade['quantity']
        else:
            summarized_trades.append(current_trade)
    return summarized_trades

# Function to execute trades on Binance
def execute_trade(api_key, api_secret, symbol, side, quantity, position_side):
    base_url = 'https://api.binance.com'
    endpoint = '/api/v3/order'
    params = {
        'symbol': symbol,
        'side': side,
        'type': 'MARKET',
        'quantity': quantity,
        'positionSide': position_side,
        'timestamp': int(time.time() * 1000)
    }
    query_string = '&'.join([f"{key}={value}" for key, value in params.items()])
    signature = hmac.new(api_secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    params['signature'] = signature
    headers = {
        'X-MBX-APIKEY': api_key
    }
    response = requests.post(base_url + endpoint, headers=headers, params=params)
    return response.json()

# Streamlit Web Interface
st.title("Binance Copy Trading Bot")
st.header("Enter your API details and settings")

api_key = st.text_input("API Key")
api_secret = st.text_input("API Secret", type="password")
leverage = st.number_input("Leverage", min_value=1, max_value=125)
trader_portfolio = st.text_input("Trader Portfolio URL")
trader_portfolio_sum = st.number_input("Trader Portfolio Sum")
own_portfolio_sum = st.number_input("Own Portfolio Sum")

# Example API endpoint for fetching trade data
api_endpoint = "https://www.binance.com/bapi/copytrading/v1/public/copytrader/trade-orders"

copy_trading_active = False

if st.button("Start Copy Trading"):
    copy_trading_active = True
    st.write("Started Copy Trading")

while copy_trading_active:
    trades = fetch_trade_data(api_endpoint, trader_portfolio)
    summarized_trades = summarize_trades(trades)
    for trade in summarized_trades:
        side = 'BUY' if 'Buy/long' in trade['side'] else 'SELL'
        position_side = 'LONG' if 'long' in trade['side'] else 'SHORT'
        quantity = trade['quantity'] * (own_portfolio_sum / trader_portfolio_sum)
        execute_trade(api_key, api_secret, trade['symbol'], side, quantity, position_side)
    time.sleep(2)

if st.button("Stop Copy Trading"):
    copy_trading_active = False
    st.write("Stopped Copy Trading")
    # Implement stop functionality

# To set leverage
if st.button("Set Leverage"):
    base_url = 'https://api.binance.com'
    endpoint = '/sapi/v1/margin/max-leverage'
    params = {
        'leverage': leverage,
        'timestamp': int(time.time() * 1000)
    }
    query_string = '&'.join([f"{key}={value}" for key, value in params.items()])
    signature = hmac.new(api_secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    params['signature'] = signature
    headers = {
        'X-MBX-APIKEY': api_key
    }
    response = requests.post(base_url + endpoint, headers=headers, params=params)
    st.write(response.json())
