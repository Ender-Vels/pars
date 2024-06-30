import streamlit as st
import requests
import json
import time
from datetime import datetime, timedelta
from binance.client import Client

# Встановлення API ключів
st.sidebar.header("API ключі")
api_key = st.sidebar.text_input("API ключ")
api_secret = st.sidebar.text_input("Секретний ключ")
client = Client(api_key, api_secret)

# Встановлення параметрів
st.header("Налаштування копіювання")
trader_url = st.text_input("Посилання на трейдера")
trader_balance = st.number_input("Баланс трейдера", min_value=0.00)
user_balance = st.number_input("Баланс власного портфеля", min_value=0.00)
leverage = st.number_input("Кредитне плече", min_value=1.00)
close_only_mode = st.checkbox("Тільки закриття угод")
reverse_mode = st.checkbox("Копіювання угод в зворотному напрямку")

# Функція для парсингу даних з розділу "Мережа" на сторінці трейдера
def parse_trade_history(trader_url):
    response = requests.get(trader_url)
    html = response.text
    start_index = html.find('"trades":') + len('"trades":')
    end_index = html.find(']"', start_index) + 1
    trade_data = html[start_index:end_index]
    trade_data = json.loads(trade_data)
    return trade_data

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

# Функція для отримання об'єму угоди
def get_trade_volume(trade, trader_balance, user_balance):
    if trade["side"] == "Open long" or trade["side"] == "Buy/long" or trade["side"] == "Open short" or trade["side"] == "Buy/short":
        return (trade["quantity"] * user_balance) / trader_balance
    else:
        return ((trade["quantity"] * user_balance) / trader_balance) * 1.05

# Функція для відкриття угоди
def open_trade(trade, trade_volume, leverage, symbol, side, position_side):
    if close_only_mode and (trade["side"] == "Open long" or trade["side"] == "Open short"):
        return
    if reverse_mode:
        if trade["side"] == "Open long" or trade["side"] == "Buy/long":
            side = "SELL"
            position_side = "SHORT"
        elif trade["side"] == "Close long" or trade["side"] == "Sell/Short":
            side = "BUY"
            position_side = "SHORT"
        elif trade["side"] == "Open short" or trade["side"] == "Buy/short":
            side = "BUY"
            position_side = "LONG"
        elif trade["side"] == "Close short" or trade["side"] == "Buy/Long":
            side = "SELL"
            position_side = "LONG"
    # Перевірка умов відкриття угоди
    if trade["side"] == "Open long" or trade["side"] == "Buy/long":
        if trade["realizedProfit"] == 0.0000000 and datetime.now() - timedelta(minutes=1) < datetime.fromtimestamp(int(trade["time"]) / 1000):
            order = client.create_margin_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=trade_volume,
                positionSide=position_side,
                isIsolated="false"
            )
            st.write(f"Відкрито {trade_volume} {trade['quantityAsset']} {position_side} по {symbol}")
    elif trade["side"] == "Close long" or trade["side"] == "Sell/Short":
        if trade["realizedProfit"] != 0.0000000:
            order = client.create_margin_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=trade_volume,
                positionSide=position_side,
                isIsolated="false"
            )
            st.write(f"Закрито {trade_volume} {trade['quantityAsset']} {position_side} по {symbol}")
    elif trade["side"] == "Open short" or trade["side"] == "Buy/short":
        if trade["realizedProfit"] == 0.0000000 and datetime.now() - timedelta(minutes=1) < datetime.fromtimestamp(int(trade["time"]) / 1000):
            order = client.create_margin_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=trade_volume,
                positionSide=position_side,
                isIsolated="false"
            )
            st.write(f"Відкрито {trade_volume} {trade['quantityAsset']} {position_side} по {symbol}")
    elif trade["side"] == "Close short" or trade["side"] == "Buy/Long":
        if trade["realizedProfit"] != 0.0000000:
            order = client.create_margin_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=trade_volume,
                positionSide=position_side,
                isIsolated="false"
            )
            st.write(f"Закрито {trade_volume} {trade['quantityAsset']} {position_side} по {symbol}")

# Основний цикл програми
if api_key and api_secret:
    # Встановлення максимального кредитного плеча
    client.API_URL = 'https://api.binance.com'
    try:
        response = client.post('/sapi/v1/margin/max-leverage', data={'symbol': 'BTCUSDT', 'leverage': leverage})
        if response:
            st.write(f"Кредитне плече успішно встановлено: {leverage}")
        else:
            st.write(f"Помилка встановлення кредитного плеча: {response}")
    except Exception as e:
        st.write(f"Помилка: {e}")

    # Додаємо кнопку запуску/зупинки
    is_running = False
    start_button = st.button("Запустити парсинг")
    stop_button = st.button("Зупинити парсинг")

    if start_button:
        is_running = True
        st.write("Парсинг запущено!")

    if stop_button:
        is_running = False
        st.write("Парсинг зупинено!")

    while is_running:
        # Парсинг даних з розділу "Мережа"
        try:
            trade_data = parse_trade_history(trader_url)
            aggregated_trades = aggregate_trades(trade_data, 2)
            for trade in aggregated_trades:
                symbol = trade["symbol"]
                trade_volume = get_trade_volume(trade, trader_balance, user_balance)
                # Визначення бокової позиції (LONG/SHORT) та типу угоди (BUY/SELL)
                side = "BUY"
                position_side = "LONG"
                open_trade(trade, trade_volume, leverage, symbol, side, position_side)
            time.sleep(5)
        except Exception as e:
            st.write(f"Помилка: {e}")

# Вивід інформації
if trader_url:
    st.write(f"Посилання на трейдера: {trader_url}")
    st.write(f"Баланс трейдера: {trader_balance}")
    st.write(f"Баланс власного портфеля: {user_balance}")
    st.write(f"Кредитне плече: {leverage}")
    st.write(f"Тільки закриття угод: {close_only_mode}")
    st.write(f"Копіювання угод в зворотному напрямку: {reverse_mode}")