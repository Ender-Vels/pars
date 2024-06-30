import streamlit as st
import requests
import time
from binance.client import Client
from binance.enums import SIDE_BUY, SIDE_SELL
from requests.exceptions import JSONDecodeError

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
client = None
if api_key and api_secret:
    try:
        st.write("Ініціалізація клієнта Binance...")
        client = Client(api_key, api_secret)
        # Виконання тестового запиту для перевірки ключів
        client.get_account()
        st.success("Клієнт Binance ініціалізований успішно.")
    except Exception as e:
        st.error(f"Помилка ініціалізації Binance клієнта: {e}")

def get_trade_history(link):
    try:
        response = requests.get(link)
        response.raise_for_status()
        st.write("Отримано відповідь від сервера: ", response.text)  # Додано відладкове повідомлення
        return response.json()
    except JSONDecodeError as e:
        st.error(f"Помилка декодування JSON: {e}")
    except requests.RequestException as e:
        st.error(f"Помилка HTTP запиту: {e}")
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

if st.button("Start Copy Trading") and client:
    while True:
        trade_history = get_trade_history(portfolio_link)
        if trade_history:
            copy_trades(trade_history)
        time.sleep(update_interval)
else:
    st.warning("Будь ласка, введіть валідні API ключі та посилання на портфель трейдера.")
