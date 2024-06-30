import streamlit as st
import requests
import json
import time
from datetime import datetime, timedelta
from binance.client import Client
from binance.enums import *
import threading
'''
# Введення API ключа та секретного ключа
st.sidebar.header("API ключі")
api_key = st.sidebar.text_input("API ключ")
api_secret = st.sidebar.text_input("Секретний ключ", type="password")

# Функція для перевірки працездатності ключів
def check_api_keys(api_key, api_secret):
    try:
        client = Client(api_key, api_secret)
        client.futures_account()
        return True
    except Exception as e:
        st.error(f"Помилка валідації API ключів: {str(e)}")
        return False

# Встановлення параметрів копіювання угод
st.header("Налаштування копіювання угод")
trader_url = st.text_input("Посилання на трейдера")
trader_balance = st.number_input("Баланс трейдера", min_value=0.00)
user_balance = st.number_input("Баланс власного портфеля", min_value=0.00)
leverage = st.number_input("Кредитне плече", min_value=1.00)
close_only_mode = st.checkbox("Тільки закриття угод")
reverse_mode = st.checkbox("Копіювати угоди в зворотньому напрямку")

# Функція для парсингу даних з веб-сторінки трейдера
def parse_trade_history(trader_url):
    try:
        response = requests.get(trader_url)
        response.raise_for_status()  # Піднімає помилку, якщо HTTP-відповідь не 200 OK
        html = response.text
        start_index = html.find('"trades":') + len('"trades":')
        end_index = html.find(']"', start_index) + 1
        trade_data = html[start_index:end_index]
        trade_data = json.loads(trade_data)
        return trade_data
    except (requests.RequestException, json.JSONDecodeError) as e:
        st.write(f"Помилка при отриманні даних з трейдера: {str(e)}")
        return []

# Функція для об'єднання дрібних транзакцій в одну угоду
def aggregate_trades(trade_data, time_interval):
    aggregated_trades = []
    current_trade = {
        "time": 0,
        "symbol": "",
        "side": "",
        "quantity": 0,
        "quantityAsset": ""
    }
    last_trade_time = 0
    for trade in trade_data:
        trade_time = int(trade["time"]) / 1000
        if trade_time - last_trade_time > time_interval:
            if current_trade["quantity"] != 0:
                aggregated_trades.append(current_trade)
            current_trade = {
                "time": trade_time,
                "symbol": trade["symbol"],
                "side": trade["side"],
                "quantity": trade["quantity"],
                "quantityAsset": trade["quantityAsset"]
            }
        else:
            current_trade["quantity"] += trade["quantity"]
        last_trade_time = trade_time
    if current_trade["quantity"] != 0:
        aggregated_trades.append(current_trade)
    return aggregated_trades

# Функція для обчислення обсягу торгівлі для відкриття угоди
def get_trade_volume(trade, trader_balance, user_balance):
    multiplier = 1.05 if trade["side"] == "Close long" or trade["side"] == "Sell/Short" else 1.0
    return (trade["quantity"] * user_balance / trader_balance) * multiplier

# Функція для відкриття угоди
def open_trade(client, trade, trade_volume, leverage, symbol, side, position_side):
    try:
        if close_only_mode and (trade["side"] == "Open long" or trade["side"] == "Open short"):
            return
        if reverse_mode:
            if trade["side"] in ["Open long", "Buy/long"]:
                side = "SELL"
                position_side = "SHORT"
            elif trade["side"] in ["Close long", "Sell/Short"]:
                side = "BUY"
                position_side = "SHORT"
            elif trade["side"] in ["Open short", "Buy/short"]:
                side = "BUY"
                position_side = "LONG"
            elif trade["side"] in ["Close short", "Buy/Long"]:
                side = "SELL"
                position_side = "LONG"
        
        # Опції відкриття угоди
        if trade["side"] in ["Open long", "Buy/long"]:
            if trade["realizedProfit"] == 0.0000000 and datetime.now() - timedelta(minutes=1) < datetime.fromtimestamp(int(trade["time"]) / 1000):
                order = client.futures_create_order(
                    symbol=symbol,
                    side=side,
                    type='MARKET',
                    quantity=trade_volume,
                    positionSide=position_side
                )
                st.write(f"Відкрито {trade_volume} {trade['quantityAsset']} {position_side} для {symbol}")
        elif trade["side"] in ["Close long", "Sell/Short"]:
            if trade["realizedProfit"] != 0.0000000:
                order = client.futures_create_order(
                    symbol=symbol,
                    side=side,
                    type='MARKET',
                    quantity=trade_volume,
                    positionSide=position_side
                )
                st.write(f"Закрито {trade_volume} {trade['quantityAsset']} {position_side} для {symbol}")
        elif trade["side"] in ["Open short", "Buy/short"]:
            if trade["realizedProfit"] == 0.0000000 and datetime.now() - timedelta(minutes=1) < datetime.fromtimestamp(int(trade["time"]) / 1000):
                order = client.futures_create_order(
                    symbol=symbol,
                    side=side,
                    type='MARKET',
                    quantity=trade_volume,
                    positionSide=position_side
                )
                st.write(f"Відкрито {trade_volume} {trade['quantityAsset']} {position_side} для {symbol}")
        elif trade["side"] in ["Close short", "Buy/Long"]:
            if trade["realizedProfit"] != 0.0000000:
                order = client.futures_create_order(
                    symbol=symbol,
                    side=side,
                    type='MARKET',
                    quantity=trade_volume,
                    positionSide=position_side
                )
                st.write(f"Закрито {trade_volume} {trade['quantityAsset']} {position_side} для {symbol}")
    except Exception as e:
        st.write(f"Помилка під час відкриття угоди: {str(e)}")

# Функція для закриття угоди
def close_trade(client, trade, symbol, side, position_side):
    try:
        if reverse_mode:
            if trade["side"] in ["Open long", "Buy/long"]:
                side = "SELL"
                position_side = "SHORT"
            elif trade["side"] in ["Close long", "Sell/Short"]:
                side = "BUY"
                position_side = "SHORT"
            elif trade["side"] in ["Open short", "Buy/short"]:
                side = "BUY"
                position_side = "LONG"
            elif trade["side"] in ["Close short", "Buy/Long"]:
                side = "SELL"
                position_side = "LONG"
        
        # Опції закриття угоди
        if trade["side"] in ["Close long", "Sell/Short"]:
            order = client.futures_create_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=trade["quantity"],
                positionSide=position_side
            )
            st.write(f"Закрито {trade['quantity']} {trade['quantityAsset']} {position_side} для {symbol}")
        elif trade["side"] in ["Close short", "Buy/Long"]:
            order = client.futures_create_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=trade["quantity"],
                positionSide=position_side
            )
            st.write(f"Закрито {trade['quantity']} {trade['quantityAsset']} {position_side} для {symbol}")
    except Exception as e:
        st.write(f"Помилка під час закриття угоди: {str(e)}")

# Функція для основного циклу копіювання угод
def start_trading(api_key, api_secret):
    client = Client(api_key, api_secret)
    while True:
        try:
            trade_data = parse_trade_history(trader_url)
            aggregated_trades = aggregate_trades(trade_data, 2)
            for trade in aggregated_trades:
                symbol = trade["symbol"]
                trade_volume = get_trade_volume(trade, trader_balance, user_balance)
                side = "BUY"
                position_side = "LONG"
                
                if trade["side"] in ["Close long", "Sell/Short"]:
                    close_trade(client, trade, symbol, side, position_side)
                elif trade["side"] in ["Close short", "Buy/Long"]:
                    close_trade(client, trade, symbol, side, position_side)
                else:
                    open_trade(client, trade, trade_volume, leverage, symbol, side, position_side)
                    
            time.sleep(5)
        except Exception as e:
            st.write(f"Помилка в основному циклі програми: {str(e)}")

# Функція для зупинки основного циклу
def stop_trading():
    st.session_state.is_running = False
    st.success("Програма зупинена")

# Кнопка запуску програми
if st.button("Запустити програму"):
    if not (api_key and api_secret and trader_url):
        st.warning("Будь ласка, введіть всі необхідні дані")
    elif not check_api_keys(api_key, api_secret):
        st.warning("Недійсні API ключі")
    else:
        try:
            st.session_state.is_running = True
            trading_thread = threading.Thread(target=start_trading, args=(api_key, api_secret))
            trading_thread.daemon = True
            trading_thread.start()
            st.success("Програма запущена у фоновому режимі")
        except Exception as e:
            st.error(f"Помилка підключення до API: {str(e)}")

# Кнопка зупинки програми
if st.button("Зупинити програму"):
    if hasattr(st.session_state, 'is_running') and st.session_state.is_running:
        stop_trading()

# Виведення інформації про налаштування копіювання угод
if trader_url:
    st.write(f"Посилання на трейдера: {trader_url}")
    st.write(f"Баланс трейдера: {trader_balance}")
    st.write(f"Баланс власного портфеля: {user_balance}")
    st.write(f"Кредитне плече: {leverage}")
    st.write(f"Тільки закриття угод: {'Так' if close_only_mode else 'Ні'}")
    st.write(f"Копіювати угоди в зворотньому напрямку: {'Так' if reverse_mode else 'Ні'}")
    '''


# Function to fetch data from the futures wallet API
def fetch_futures_wallet(api_url, headers):
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to fetch data from the API")
        return None

# Function to display the fetched data
def display_wallet_data(wallet_data):
    st.title("Futures Wallet Data")

    if wallet_data:
        st.subheader("Wallet Information")
        st.json(wallet_data)
    else:
        st.error("No data to display")

# Main function to run the Streamlit app
def main():
    st.sidebar.title("Futures Wallet Checker")

    api_url = st.sidebar.text_input("API URL", "https://api.example.com/futures_wallet")
    api_key = st.sidebar.text_input("API Key", type="password")

    if st.sidebar.button("Fetch Wallet Data"):
        headers = {"Authorization": f"Bearer {api_key}"}
        wallet_data = fetch_futures_wallet(api_url, headers)
        display_wallet_data(wallet_data)

if __name__ == "__main__":
    main()
