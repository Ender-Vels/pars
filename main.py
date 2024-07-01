import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time
import requests
from binance.client import Client
from bs4 import BeautifulSoup
import json

# Налаштування API Binance
api_key = st.text_input("API Key")
api_secret = st.text_input("API Secret", type="password")
client = Client(api_key, api_secret)

# Введення посилання трейдера та розмірів портфоліо
trader_link = st.text_input("Trader Link")
my_portfolio_size = st.number_input("My Portfolio Size", min_value=0.0, step=1.0)
trader_portfolio_size = st.number_input("Trader Portfolio Size", min_value=0.0, step=1.0)

# Кнопки для керування скрапінгом
start_button = st.button("Start Scraping")
stop_button = st.button("Stop Scraping")
close_only_mode = st.checkbox("Close-Only Mode")
reverse_trade_copy = st.checkbox("Reverse Trade Copy")

# Прапорець для керування процесом
running = False

def initialize_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options)
    return driver

def accept_cookies(driver):
    time.sleep(2)
    try:
        driver.find_element(By.ID, "onetrust-accept-btn-handler").click()
        time.sleep(2)
    except:
        pass

def navigate_to_trade_history(driver):
    time.sleep(2)
    driver.find_element(By.CSS_SELECTOR, "#tab-tradeHistory > div").click()
    time.sleep(2)

def scrape_last_order(driver):
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    order_table = soup.select_one(".css-g5h8k8 > div > div > div > table > tbody > tr:nth-child(1)")
    if order_table:
        return {
            "time": order_table.select_one("td:nth-child(1)").text,
            "price": order_table.select_one("td:nth-child(4)").text,
            "quantity": order_table.select_one("td:nth-child(5)").text
        }
    return None

def find_last_order(driver):
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    orders = []
    for i in range(1, 11):
        row = soup.select_one(f"div.card-outline.css-1tacewb > div > div.css-gnqbje > div > div > div.css-g5h8k8 > div > div > div > table > tbody > tr:nth-child({i})")
        if row:
            orders.append({
                "time": row.select_one("td:nth-child(1)").text,
                "symbol": row.select_one("td:nth-child(2)").text.split(" ")[0],
                "side": row.select_one("td:nth-child(3)").text,
                "price": row.select_one("td:nth-child(4)").text,
                "quantity": row.select_one("td:nth-child(5)").text
            })
    return orders

def process_order(order, client, my_portfolio_size, trader_portfolio_size):
    symbol = order["symbol"]
    side = "BUY" if order["side"] in ["Open long", "Close short", "Buy/Long"] else "SELL"
    quantity = float(order["quantity"].replace(",", ""))
    adjusted_quantity = (my_portfolio_size * quantity) / trader_portfolio_size

    order_params = {
        "symbol": symbol,
        "side": side,
        "type": "MARKET",
        "quantity": adjusted_quantity,
        "leverage": 20
    }
    client.futures_create_order(**order_params)

def main():
    global running
    if start_button:
        running = True
        driver = initialize_driver()
        driver.get(trader_link)
        accept_cookies(driver)
        navigate_to_trade_history(driver)
        last_order = scrape_last_order(driver)

        while running:
            orders = find_last_order(driver)
            for order in orders:
                if order["time"] != last_order["time"]:
                    process_order(order, client, my_portfolio_size, trader_portfolio_size)
                    last_order = order
            time.sleep(2)

        driver.quit()

    if stop_button:
        running = False

if __name__ == "__main__":
    main()
