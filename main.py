import streamlit as st
import requests
import time
import hmac
import hashlib
from urllib.parse import urlencode

# Streamlit UI
st.title("Binance Copy Trading Bot")
st.write("Automatically copy trades from a Binance trader and execute them in your portfolio.")

api_key = st.text_input("Your Binance API Key")
api_secret = st.text_input("Your Binance API Secret", type="password")
trader_api_endpoint = st.text_input("Trader API Endpoint")
leverage = st.number_input("Leverage", min_value=1, max_value=125, value=1)
trader_portfolio_value = st.number_input("Trader Portfolio Value", min_value=0.0, value=1000.0)
your_portfolio_value = st.number_input("Your Portfolio Value", min_value=0.0, value=1000.0)

only_close_trades = st.checkbox("Only Close Trades")
reverse_trades = st.checkbox("Reverse Trades")

start_button = st.button("Start Copy Trading")

# Binance API endpoints
base_url = "https://api.binance.com"

def create_signature(query_string, secret):
    return hmac.new(secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

def binance_request(method, endpoint, params=None):
    headers = {
        "X-MBX-APIKEY": api_key
    }
    query_string = urlencode(params) if params else ''
    signature = create_signature(query_string, api_secret)
    url = f"{base_url}{endpoint}?{query_string}&signature={signature}"
    response = requests.request(method, url, headers=headers)
    return response.json()

def get_trader_trades(trader_api_endpoint):
    try:
        response = binance_request("GET", trader_api_endpoint)
        trades = response.get("trades", [])
        return trades
    except Exception as e:
        st.error(f"Error fetching trader trades: {str(e)}")
        return []

def aggregate_trades(trades):
    aggregated_trades = {}
    current_time = int(time.time() * 1000)
    for trade in trades:
        trade_time = int(trade["time"])
        if current_time - trade_time <= 2000:
            key = (trade["symbol"], trade["side"])
            if key not in aggregated_trades:
                aggregated_trades[key] = trade
            else:
                aggregated_trades[key]["quantity"] += trade["quantity"]
                aggregated_trades[key]["price"] = (aggregated_trades[key]["price"] + trade["price"]) / 2
    return list(aggregated_trades.values())

def execute_trade(trade, position_side):
    side = "BUY" if trade["side"] == "buy" else "SELL"
    if reverse_trades:
        side = "SELL" if side == "BUY" else "BUY"
    params = {
        "symbol": trade["symbol"],
        "side": side,
        "type": "MARKET",
        "quantity": trade["quantity"],
        "positionSide": position_side,
        "timestamp": int(time.time() * 1000)
    }
    response = binance_request("POST", "/api/v3/order", params)
    return response

def main():
    if start_button:
        last_trade_time = 0
        while True:
            trades = get_trader_trades(trader_api_endpoint)
            if trades:
                new_trades = [trade for trade in trades if int(trade["time"]) > last_trade_time]
                if new_trades:
                    aggregated_trades = aggregate_trades(new_trades)
                    for trade in aggregated_trades:
                        if trade["side"] in ["buy", "long"]:
                            if not only_close_trades:
                                execute_trade(trade, "LONG")
                        elif trade["side"] in ["sell", "short"]:
                            execute_trade(trade, "LONG")
                        elif trade["side"] in ["buy", "long"]:
                            if not only_close_trades:
                                execute_trade(trade, "SHORT")
                        elif trade["side"] in ["sell", "long"]:
                            execute_trade(trade, "SHORT")
                    last_trade_time = int(new_trades[-1]["time"])
            time.sleep(2)

if __name__ == "__main__":
    main()
