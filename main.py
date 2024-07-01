import streamlit as st
import time
import csv
import re
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup

class ScrapeTask:
    def __init__(self):
        self.driver = None

    def initialize_driver(self):
        try:
            chromedriver_autoinstaller.install()  # Встановлення chromedriver автоматично
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            self.driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            st.error(f"Error initializing WebDriver: {e}")
            st.stop()

    def start_scraping(self, link):
        try:
            self.driver.get(link)
            self.accept_cookies()
            self.navigate_to_trade_history()
            self.scrape_and_show()
        except Exception as e:
            st.error(f"Error scraping data: {e}")
        finally:
            if self.driver:
                self.driver.quit()

    def accept_cookies(self):
        try:
            time.sleep(2)
            accept_btn = self.find_element_with_retry(By.ID, "onetrust-accept-btn-handler")
            accept_btn.click()
            time.sleep(2)
        except Exception as e:
            st.warning(f"Warning: Error accepting cookies: {e}")

    def navigate_to_trade_history(self):
        try:
            move_to_trade_history = self.find_element_with_retry(By.CSS_SELECTOR, "#tab-tradeHistory > div")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", move_to_trade_history)
            move_to_trade_history.click()
            time.sleep(2)
        except Exception as e:
            st.warning(f"Warning: Trade history tab not found: {e}")

    def scrape_and_show(self):
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            orders = soup.select(".css-g5h8k8 > div > div > div > table > tbody > tr")
            
            if not orders:
                st.warning("Warning: No trade history orders found.")
                return
            
            st.write("Trade History:")
            st.write("Time\tSymbol\tSide\tPrice\tQuantity")
            for order in orders:
                symbol = order.select_one("td:nth-child(2)").text.strip()
                symbol = re.sub(r'(\S)Perpetual\b', r'\1 Perpetual', symbol).strip()
                time = order.select_one("td:nth-child(1)").text.strip()
                side = order.select_one("td:nth-child(3)").text.strip()
                price = order.select_one("td:nth-child(4)").text.strip()
                quantity = order.select_one("td:nth-child(5)").text.strip()
                st.write(f"{time}\t{symbol}\t{side}\t{price}\t{quantity}")

        except Exception as e:
            st.error(f"Error scraping and showing data: {e}")

    def find_element_with_retry(self, by, selector, max_attempts=3):
        attempts = 0
        while attempts < max_attempts:
            try:
                element = self.driver.find_element(by, selector)
                return element
            except Exception as e:
                attempts += 1
                st.warning(f"Warning: Error finding element {selector} (Attempt {attempts}/{max_attempts}): {e}")
                time.sleep(2)
        raise NoSuchElementException(f"Element {selector} not found after {max_attempts} attempts")

# Main Streamlit application
def main():
    st.title("Trade History Scraper")

    link = st.text_input("Enter the Binance trade history link:")
    if st.button("Start Scraping"):
        if link:
            scraper = ScrapeTask()
            scraper.initialize_driver()
            scraper.start_scraping(link)
        else:
            st.warning("Please enter a Binance trade history link.")

if __name__ == "__main__":
    main()
