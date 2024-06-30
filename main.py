import streamlit as st
import requests
import time
from binance.client import Client
from binance.enums import SIDE_BUY, SIDE_SELL

# Введіть ваші Binance API ключі тут
api_key = st.text_input("Binance API Key")
api_secret = st.text_input("Binance API Secret", type="password")

# Введіть посилання на портфель трейдера
portfolio_link = st.text_input("Trader's Portfolio Link")

# Введіть ваш розмір портфелю
your_portfolio_size = st.number_input("Your Portfolio Size", min_value=0.0, step=0.1)

# Введіть інтервал оновлення в секундах
update_interval = st.number_input("Update Interval (seconds)", min_value=1, step=1, value=2)

# Ініціалізація Binance клієнта
if api_key and api_secret:
    client = Client(api_key, api_secret)

def get_trade_history(link):
    response = requests.get(link)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Не вдалося отримати дані з посилання.")
        return None

def copy_trades(trades):
    for trade in trades:
        symbol = trade['symbol']
        side = SIDE_BUY if trade['side'] == 'buy' else SIDE_SELL
        quantity = trade['quantity']
        price = trade['price']
        
        # Виконання угоди на Binance
        try:
            order = client.create_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=quantity
            )
            st.write(f"Угода виконана: {order}")
        except Exception as e:
            st.error(f"Помилка при виконанні угоди: {e}")

if st.button("Start Copy Trading"):
    while True:
        trade_history = get_trade_history(portfolio_link)
        if trade_history:
            copy_trades(trade_history)
        time.sleep(update_interval)
