import streamlit as st
import requests
import json
import time
from datetime import datetime, timedelta
from binance.client import Client

# Ініціалізація стану сесії для зберігання даних
if 'session_data' not in st.session_state:
    st.session_state.session_data = {
        'api_key': '',
        'api_secret': '',
        'trader_url': '',
        'trader_balance': 0.0,
        'user_balance': 0.0,
        'leverage': 1.0,
        'close_only_mode': False,
        'reverse_mode': False,
        'is_running': False,
        'client': None
    }

# Введення API ключів та інших параметрів
st.sidebar.header("API ключі")
api_key = st.sidebar.text_input("API ключ", value=st.session_state.session_data['api_key'])
api_secret = st.sidebar.text_input("Секретний ключ", value=st.session_state.session_data['api_secret'])

st.header("Налаштування копіювання")
trader_url = st.text_input("Посилання на трейдера", value=st.session_state.session_data['trader_url'])
trader_balance = st.number_input("Баланс трейдера", min_value=0.00, value=st.session_state.session_data['trader_balance'])
user_balance = st.number_input("Баланс власного портфеля", min_value=0.00, value=st.session_state.session_data['user_balance'])
leverage = st.number_input("Кредитне плече", min_value=1.00, value=st.session_state.session_data['leverage'])
close_only_mode = st.checkbox("Тільки закриття угод", value=st.session_state.session_data['close_only_mode'])
reverse_mode = st.checkbox("Копіювання угод в зворотньому напрямку", value=st.session_state.session_data['reverse_mode'])

# Зберігання введених даних в стані сесії
st.session_state.session_data['api_key'] = api_key
st.session_state.session_data['api_secret'] = api_secret
st.session_state.session_data['trader_url'] = trader_url
st.session_state.session_data['trader_balance'] = trader_balance
st.session_state.session_data['user_balance'] = user_balance
st.session_state.session_data['leverage'] = leverage
st.session_state.session_data['close_only_mode'] = close_only_mode
st.session_state.session_data['reverse_mode'] = reverse_mode

# Підключення до Binance API тільки після натискання кнопки
if api_key and api_secret:
    st.session_state.session_data['client'] = Client(api_key, api_secret)

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
    client = st.session_state.session_data['client']
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

# Основна функція для парсингу та відкриття угод
def main_parsing_loop():
    while st.session_state.session_data['is_running']:
        # Парсинг даних з розділу "Мережа"
        try:
            trade_data = parse_trade_history(trader_url)
            aggregated_trades = aggregate_trades(trade_data, 2)
            for trade in aggregated_trades:
                trade_volume = get_trade_volume(trade, trader_balance, user_balance)
                open_trade(trade, trade_volume, leverage, trade["symbol"], trade["side"], trade["positionSide"])
        except Exception as e:
            st.error(f"Помилка парсингу або відкриття угоди: {e}")
        time.sleep(2)

# Відображення кнопок управління
if st.button('Почати парсинг'):
    st.session_state.session_data['is_running'] = True
    main_parsing_loop()

if st.button('Зупинити парсинг'):
    st.session_state.session_data['is_running'] = False

# Відображення статусу парсингу
if st.session_state.session_data['is_running']:
    st.write("Парсинг запущено.")
else:
    st.write("Парсинг зупинено.")
