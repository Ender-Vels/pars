import time
import csv
import re
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup

class ScrapeTask:
    def __init__(self, taskDTO):
        self.taskDTO = taskDTO
        self.driver = None
        self.processed_orders = set()  # Set to store processed orders
        self.scraping = False

    def initialize_driver(self):
        try:
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.get(self.taskDTO['link'])
        except Exception as e:
            print(f"Error initializing WebDriver: {e}")

    def start_scraping(self):
        self.scraping = True
        self.accept_cookies()
        self.navigate_to_trade_history()
        self.scrape_and_display_data()

    def stop_scraping(self):
        self.scraping = False
        if self.driver:
            self.driver.quit()

    def accept_cookies(self):
        try:
            time.sleep(2)
            accept_btn = self.find_element_with_retry(By.ID, "onetrust-accept-btn-handler")
            accept_btn.click()
            time.sleep(2)
        except NoSuchElementException:
            print("Trying alternative selector for accept cookies button.")
            try:
                accept_btn = self.find_element_with_retry(By.CSS_SELECTOR, ".accept-btn-handler")
                accept_btn.click()
                time.sleep(2)
            except Exception as e:
                print(f"Error accepting cookies: {e}")

    def navigate_to_trade_history(self):
        try:
            move_to_trade_history = self.find_element_with_retry(By.CSS_SELECTOR, "#tab-tradeHistory > div")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", move_to_trade_history)
            move_to_trade_history.click()
            time.sleep(2)
        except Exception as e:
            print(f"Trade history tab not found: {e}")
            self.driver.refresh()
            self.navigate_to_trade_history()

    def scrape_and_display_data(self):
        try:
            while self.scraping:
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                orders = soup.select(".css-g5h8k8 > div > div > div > table > tbody > tr")
                new_data = []

                for order in orders:
                    symbol = order.select_one("td:nth-child(2)").text.strip()
                    
                    # Add space before 'Perpetual' and remove 'Perpetual' if it follows a space
                    symbol = re.sub(r'\sPerpetual\b', '', symbol)

                    time_ = order.select_one("td:nth-child(1)").text.strip()
                    side = order.select_one("td:nth-child(3)").text.strip()
                    price = order.select_one("td:nth-child(4)").text.strip()
                    quantity = order.select_one("td:nth-child(5)").text.strip()

                    # Check if order already processed
                    order_id = f"{time_}-{symbol}-{side}-{price}-{quantity}"
                    if order_id not in self.processed_orders:
                        new_data.append([time_, symbol, side, price, quantity])
                        self.processed_orders.add(order_id)

                if new_data:
                    st.write(new_data)

                next_page_button = self.find_element_with_retry(By.CSS_SELECTOR, "div.bn-pagination-next")
                self.driver.execute_script("arguments[0].scrollIntoView(true);", next_page_button)
                next_page_button.click()
                time.sleep(2)

        except Exception as e:
            print(f"Error scraping and displaying data: {e}")

        finally:
            self.driver.quit()

    def find_element_with_retry(self, by, selector, max_attempts=3):
        attempts = 0
        while attempts < max_attempts:
            try:
                element = self.driver.find_element(by, selector)
                return element
            except Exception as e:
                attempts += 1
                print(f"Error finding element {selector} (Attempt {attempts}/{max_attempts}): {e}")
                time.sleep(2)
        raise NoSuchElementException(f"Element {selector} not found after {max_attempts} attempts")

# Streamlit UI
st.title("Binance Trade History Scraper")

url = st.text_input("Enter the Binance copy trading URL:", "https://www.binance.com/en/copy-trading/lead-details/3955388570936769793")
start_button = st.button("Start Scraping")
stop_button = st.button("Stop Scraping")

scrape_task = None

if start_button:
    taskDTO = {'link': url}
    scrape_task = ScrapeTask(taskDTO)
    scrape_task.initialize_driver()
    st.write("Scraping started...")
    scrape_task.start_scraping()

if stop_button and scrape_task:
    scrape_task.stop_scraping()
    st.write("Scraping stopped.")
