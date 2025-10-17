# In ticker_utils.py
import pandas as pd
import logging
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DB_HOST = os.getenv("DB_HOST")
# ... (load all DB credentials)

def load_nse_tickers():
    """Loads the ticker map from the PostgreSQL database."""
    conn = None
    try:
        conn = psycopg2.connect(...) # Use your DB credentials
        df = pd.read_sql_query("SELECT name, ticker FROM stocks", conn)
        ticker_map = {str(name).lower(): symbol for name, symbol in zip(df['name'], df['ticker'])}
        logging.info(f"Loaded {len(ticker_map)} tickers from PostgreSQL.")
        return ticker_map
    except Exception as e:
        logging.error(f"Failed to load tickers from DB: {e}"); return {}
    finally:
        if conn: conn.close()