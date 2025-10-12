# ticker_utils.py
import pandas as pd
import logging

def load_nse_tickers(filepath="nse_stocks.csv"):
    """
    Loads the NSE stock data from the CSV and creates a mapping
    from company name to ticker symbol.
    """
    try:
        df = pd.read_csv(filepath)
        # Create a dictionary mapping: {'COMPANY NAME': 'SYMBOL'}
        # We convert the name to lowercase for case-insensitive matching
        ticker_map = {str(name).lower(): symbol for name, symbol in zip(df['NAME OF COMPANY'], df['SYMBOL'])}
        logging.info(f"Successfully loaded {len(ticker_map)} NSE tickers.")
        return ticker_map
    except FileNotFoundError:
        logging.error(f"Ticker file not found at {filepath}. Please download it from the NSE website.")
        return {}