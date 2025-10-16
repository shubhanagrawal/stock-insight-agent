# scheduler.py
import time
import logging
from worker import process_feed

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s: %(message)s')

# --- Configuration ---
FEEDS_TO_PROCESS = {
    "Moneycontrol - Top News": {'url': "https://www.moneycontrol.com/rss/MCtopnews.xml", 'weight': 1.0},
    "ET Markets - Stocks":     {'url': "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms", 'weight': 1.0},
    "Livemint - Companies":    {'url': "https://www.livemint.com/rss/companies", 'weight': 0.9},
}
RUN_INTERVAL_SECONDS = 900 # 15 minutes

if __name__ == '__main__':
    logging.info("--- Starting Scheduler ---")
    while True:
        logging.info(f"--- Starting new processing cycle ---")
        
        for name, config in FEEDS_TO_PROCESS.items():
            process_feed(feed_url=config['url'], source_weight=config['weight'])
        
        logging.info(f"--- Cycle complete. Waiting for {RUN_INTERVAL_SECONDS} seconds... ---")
        time.sleep(RUN_INTERVAL_SECONDS)