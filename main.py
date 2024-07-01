import streamlit as st
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

class LastOrder:
    def __init__(self):
        self.time = None
        self.symbol = None
        self.side = None
        self.price = None
        self.quantity = None

class ScrapeTask:
    def __init__(self, link):
        self.link = link
        self.last_order = LastOrder()
        self.driver = None

    def initialize_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.get(self.link)

    def scrape_last_order(self):
        time.sleep(2)  # Give time for the page to load
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        
        # Modify this part to scrape your specific data
        # Example:
        order_row = soup.select_one('.css-g5h8k8 > div > div > div > table > tbody > tr:nth-child(1)')
        if order_row:
            self.last_order.time = order_row.select_one('td:nth-child(1)').text.strip()
            self.last_order.symbol = order_row.select_one('td:nth-child(2)').text.strip()
            self.last_order.side = order_row.select_one('td:nth-child(3)').text.strip()
            self.last_order.price = order_row.select_one('td:nth-child(4)').text.strip()
            self.last_order.quantity = order_row.select_one('td:nth-child(5)').text.strip()
        else:
            st.error("No orders found or elements missing in the table.")

    def run(self):
        self.initialize_driver()
        self.scrape_last_order()
        self.driver.quit()

def main():
    st.title('Binance Trade Scraper')

    link = st.text_input('Enter Binance trade history URL:')
    if st.button('Start Scraping'):
        scraper = ScrapeTask(link)
        scraper.run()
        st.success('Scraping complete.')
        st.write(f'Last Order: Time={scraper.last_order.time}, Symbol={scraper.last_order.symbol}, Side={scraper.last_order.side}, Price={scraper.last_order.price}, Quantity={scraper.last_order.quantity}')

if __name__ == '__main__':
    main()
