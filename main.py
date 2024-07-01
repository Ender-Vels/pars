import streamlit as st
import requests
from bs4 import BeautifulSoup
import re

def scrape_trade_history(link):
    try:
        response = requests.get(link)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
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
        else:
            st.error(f"Error fetching trade history: Status code {response.status_code}")
    except Exception as e:
        st.error(f"Error scraping data: {e}")

# Main Streamlit application
def main():
    st.title("Trade History Scraper")

    link = st.text_input("Enter the Binance trade history link:")
    if st.button("Start Scraping"):
        if link:
            scrape_trade_history(link)
        else:
            st.warning("Please enter a Binance trade history link.")

if __name__ == "__main__":
    main()
