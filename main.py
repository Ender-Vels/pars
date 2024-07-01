import streamlit as st
import requests
import json
import time
import threading
from datetime import datetime, timedelta
from binance_f import RequestClient
from binance_f.constant.test import *
from binance_f.base.printobject import *
from binance_f.model.constant import *

# Введення API ключа та секретного ключа
st.sidebar.header("API ключі")
api_key = st.sidebar.text_input("API ключ")
api_secret = st.sidebar.text_input("Секретний ключ", type="password")

# Функція для перевірки працездатності ключів
def check_api_keys(api_key, api_secret):
    try:
        request_client = RequestClient(api_key=api_key, api_secret=api_secret)
        result = request_client.get_balance()
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
def open_trade(request_client, trade, trade_volume, leverage, symbol, side, position_side):
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
                result = request_client.post_order(
                    symbol=symbol,
                    side=side,
                    ordertype=OrderType.MARKET,  # Використовуємо OrderType.MARKET замість ORDERTYPE_MARKET
                    quantity=trade_volume,
                    positionSide=position_side
                )
                st.write(f"Відкрито {trade_volume} {trade['quantityAsset']} {position_side} для {symbol}")
        elif trade["side"] in ["Close long", "Sell/Short"]:
            if trade["realizedProfit"] != 0.0000000:
                result = request_client.post_order(
                    symbol=symbol,
                    side=side,
                    ordertype=OrderType.MARKET,  # Використовуємо OrderType.MARKET замість ORDERTYPE_MARKET
                    quantity=trade_volume,
                    positionSide=position_side
                )
                st.write(f"Закрито {trade_volume} {trade['quantityAsset']} {position_side} для {symbol}")
        elif trade["side"] in ["Open short", "Buy/short"]:
            if trade["realizedProfit"] == 0.0000000 and datetime.now() - timedelta(minutes=1) < datetime.fromtimestamp(int(trade["time"]) / 1000):
                result = request_client.post_order(
                    symbol=symbol,
                    side=side,
                    ordertype=OrderType.MARKET,  # Використовуємо OrderType.MARKET замість ORDERTYPE_MARKET
                    quantity=trade_volume,
                    positionSide=position_side
                )
                st.write(f"Відкрито {trade_volume} {trade['quantityAsset']} {position_side} для {symbol}")
        elif trade["side"] in ["Close short", "Buy/Long"]:
            if trade["realizedProfit"] != 0.0000000:
                result = request_client.post_order(
                    symbol=symbol,
                    side=side,
                    ordertype=OrderType.MARKET,  # Використовуємо OrderType.MARKET замість ORDERTYPE_MARKET
                    quantity=trade_volume,
                    positionSide=position_side
                )
                st.write(f"Закрито {trade_volume} {trade['quantityAsset']} {position_side} для {symbol}")
    except Exception as e:
        st.write(f"Помилка під час відкриття угоди: {str(e)}")

# Функція для закриття угоди
def close_trade(request_client, trade, symbol, side, position_side):
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
            if trade["realizedProfit"] != 0.0000000:
                result = request_client.post_order(
                    symbol=symbol,
                    side=side,
                    ordertype=OrderType.MARKET,  # Використовуємо OrderType.MARKET замість ORDERTYPE_MARKET
                    quantity=trade["quantity"],
                    positionSide=position_side
                )
                st.write(f"Закрито {trade['quantity']} {trade['quantityAsset']} {position_side} для {symbol}")
        elif trade["side"] in ["Close short", "Buy/Long"]:
            if trade["realizedProfit"] != 0.0000000:
                result = request_client.post_order(
                    symbol=symbol,
                    side=side,
                    ordertype=OrderType.MARKET,  # Використовуємо OrderType.MARKET замість ORDERTYPE_MARKET
                    quantity=trade["quantity"],
                    positionSide=position_side
                )
                st.write(f"Закрито {trade['quantity']} {trade['quantityAsset']} {position_side} для {symbol}")
    except Exception as e:
        st.write(f"Помилка під час закриття угоди: {str(e)}")

# Функція для парсингу та копіювання угод
def copy_trades():
    try:
        if not api_key or not api_secret:
            st.warning("Будь ласка, введіть API ключ та секретний ключ")
            return
        if not check_api_keys(api_key, api_secret):
            return
        
        request_client = RequestClient(api_key=api_key, api_secret=api_secret)
        trade_data = parse_trade_history(trader_url)
        if not trade_data:
            st.warning("Не вдалося отримати дані трейдера. Перевірте посилання на трейдера.")
            return
        
        time_interval = 2  # Інтервал часу для об'єднання транзакцій (в секундах)
        aggregated_trades = aggregate_trades(trade_data, time_interval)
        
        for trade in aggregated_trades:
            trade_volume = get_trade_volume(trade, trader_balance, user_balance)
            open_trade(request_client, trade, trade_volume, leverage, trade["symbol"], trade["side"], trade["positionSide"])
    
    except Exception as e:
        st.write(f"Помилка під час копіювання угод: {str(e)}")

# Інтерфейс користувача для керування програмою
st.header("Керування програмою")
start_copying = st.button("Почати копіювання угод")
stop_copying = st.button("Зупинити копіювання угод")

if start_copying:
    st.write("Початок копіювання угод...")
    copy_thread = threading.Thread(target=copy_trades)
    copy_thread.start()

if stop_copying:
    st.write("Зупинка копіювання угод...")
