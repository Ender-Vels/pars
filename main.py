import time
import re
import requests
from bs4 import BeautifulSoup
import streamlit as st

class ScrapeTask:
    def __init__(self, taskDTO):
        self.taskDTO = taskDTO
        self.session = requests.Session()
        self.processed_orders = set()  # Set to store processed orders
        self.scraping = False

    def start_scraping(self):
        self.scraping = True
        while self.scraping:
            try:
                response = self.session.get(self.taskDTO['link'])
                if response.status_code != 200:
                    st.error(f"Error fetching the page: {response.status_code}")
                    break

                soup = BeautifulSoup(response.content, 'html.parser')
                orders = soup.select(".css-g5h8k8 > div > div > div > table > tbody > tr")
                
                # Check if orders are found
                if not orders:
                    st.warning("No trade history orders found. Please check if the link is correct.")
                    break

                new_data = []

                for order in orders:
                    symbol = order.select_one("td:nth-child(2)").text.strip()
                    
                    # Add space before 'Perpetual' and remove 'Perpetual' if it follows a space
                    symbol = re.sub(r'(\S)Perpetual\b', r'\1 Perpetual', symbol)
                    symbol = re.sub(r'\sPerpetual\b', '', symbol).strip()

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
                    for data in new_data:
                        st.write(data)
                else:
                    st.write("No new data found.")

                # Check if the stop button was pressed
                if not st.session_state.get('scraping', True):
                    self.scraping = False
                else:
                    time.sleep(5)  # Check for new orders every 5 seconds

            except Exception as e:
                st.error(f"Error scraping and displaying data: {e}")
                self.scraping = False

# Streamlit UI
st.title("Binance Trade History Scraper")

url = st.text_input("Enter the Binance copy trading URL:", "https://www.binance.com/en/copy-trading/lead-details/3955388570936769793")
if 'scraping' not in st.session_state:
    st.session_state.scraping = False

start_button = st.button("Start Scraping")
stop_button = st.button("Stop Scraping")

if start_button:
    st.session_state.scraping = True
    taskDTO = {'link': url}
    scrape_task = ScrapeTask(taskDTO)
    st.write("Scraping started...")
    scrape_task.start_scraping()

if stop_button:
    st.session_state.scraping = False
    st.write("Scraping stopped.")
