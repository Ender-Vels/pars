import streamlit as st
import requests
import json
import time
from datetime import datetime, timedelta
from binance.client import Client
import threading

# Введення API ключа та секретного ключа
st.sidebar.header("API ключі")
api_key = st.sidebar.text_input("API ключ")
api_secret = st.sidebar.text_input("Секретний ключ", type="password")

# Встановлення параметрів копіювання угод
st.header("Налаштування копіювання угод")
trader_url = st.text_input("Посилання на трейдера")
trader_balance = st.number_input("Баланс трейдера", min_value=0.00)
user_balance = st.number_input("Баланс власного портфеля", min_value=0.00)
leverage = st.number_input("Кредитне плече", min_value=1.00)
close_only_mode = st.checkbox("Тільки закриття угод")
reverse_mode = st.checkbox("Копіювати угоди в зворотньому напрямку")

# Функція для отримання торгівельної історії з трейдера
def fetch_trade_history(trader_url):
    try:
        response = requests.get(trader_url)
        response.raise_for_status()  # Викидає помилку, якщо HTTP-відповідь не 200 OK
        trade_data = response.json()
        return trade_data
    except requests.RequestException as e:
        st.write(f"Помилка при отриманні даних з трейдера: {str(e)}")
        return []

# Функція для обробки отриманих угод
def process_trades(trade_data):
    if not trade_data:
        st.write("Немає даних для обробки.")
        return
    
    # Виведення угод для демонстрації
    st.write("Отримана торгівельна історія:")
    for trade in trade_data:
        st.write(trade)

# Функція для основного циклу копіювання угод
def start_trading(api_key, api_secret):
    client = Client(api_key, api_secret)
    while True:
        try:
            trade_data = fetch_trade_history(trader_url)
            process_trades(trade_data)
            time.sleep(5)
        except Exception as e:
            st.write(f"Помилка в основному циклі програми: {str(e)}")

# Кнопка запуску програми
if st.button("Запустити програму"):
    if not (api_key and api_secret and trader_url):
        st.warning("Будь ласка, введіть всі необхідні дані")
    else:
        try:
            trading_thread = threading.Thread(target=start_trading, args=(api_key, api_secret))
            trading_thread.daemon = True
            trading_thread.start()
            st.success("Програма запущена у фоновому режимі")
        except Exception as e:
            st.error(f"Помилка підключення до API: {str(e)}")

# Виведення інформації про налаштування копіювання угод
if trader_url:
    st.write(f"Посилання на трейдера: {trader_url}")
    st.write(f"Баланс трейдера: {trader_balance}")
    st.write(f"Баланс власного портфеля: {user_balance}")
    st.write(f"Кредитне плече: {leverage}")
    st.write(f"Тільки закриття угод: {'Так' if close_only_mode else 'Ні'}")
    st.write(f"Копіювати угоди в зворотньому напрямку: {'Так' if reverse_mode else 'Ні'}")
