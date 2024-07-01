import streamlit as st
from scrapydo import setup, run_spider
from scrapy import signals
from scrapy.signalmanager import dispatcher
from scrapy import Spider, Request

# Клас для Scrapy Spider
class BinanceSpider(Spider):
    name = 'binance'
    allowed_domains = ['binance.com']
    start_urls = ['https://www.binance.com/en/copy-trading/lead-details/3955388570936769793']

    def parse(self, response):
        last_orders = []

        # Витягнення даних
        for row in response.css('.css-g5h8k8 > div > div > div > table > tbody > tr'):
            time = row.css('td:nth-child(1)::text').get()
            symbol = row.css('td:nth-child(2)::text').get()
            side = row.css('td:nth-child(3)::text').get()
            price = row.css('td:nth-child(4)::text').get()
            quantity = row.css('td:nth-child(5)::text').get()

            last_orders.append({
                'time': time,
                'symbol': symbol,
                'side': side,
                'price': price,
                'quantity': quantity
            })

        # Передача результатів через сигнал
        dispatcher.send(signal=signals.spider_closed, sender=self, last_orders=last_orders)

# Функція для відображення даних у Streamlit
def main():
    st.title('Додаток для відображення даних Binance')

    # Налаштування та запуск Scrapy Spider
    setup()
    run_spider(BinanceSpider)

    # Отримання даних через сигнал
    @st.cache(suppress_st_warning=True)
    def display_results():
        results = dispatcher.connect(display_results_callback, signal=signals.spider_closed)
        return results

    def display_results_callback(signal, sender, **kwargs):
        last_orders = kwargs.get('last_orders', [])

        if last_orders:
            st.write("Останні замовлення:")
            st.write(last_orders)
        else:
            st.write("Дані ще не витягнуті")

    display_results()

if __name__ == '__main__':
    main()
