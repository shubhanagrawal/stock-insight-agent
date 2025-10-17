# enrich_data.py
import pandas as pd
import yfinance as yf
import logging
from time import sleep
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def enrich_stock_data():
    """
    Reads the basic NSE stock list, enriches it with sector information from
    yfinance, and saves it to a new CSV file.
    """
    try:
        df = pd.read_csv("nse_stocks.csv")
        logging.info(f"Loaded {len(df)} stocks from nse_stocks.csv")
    except FileNotFoundError:
        logging.error("nse_stocks.csv not found. Please download it first.")
        return

    sectors = []
    # Use tqdm for a nice progress bar, as this will take a while
    for ticker_symbol in tqdm(df['SYMBOL'], desc="Enriching data with sectors"):
        try:
            # Append ".NS" for Indian stocks
            ticker = yf.Ticker(f"{ticker_symbol}.NS")
            
            # .info is a dictionary containing company data
            sector = ticker.info.get('sector')
            
            if sector:
                sectors.append(sector)
            else:
                sectors.append(None) # Append None if sector is not found
            
            # Be respectful to the API and avoid getting rate-limited
            sleep(0.1) 
        except Exception as e:
            logging.warning(f"Could not fetch info for {ticker_symbol}: {e}")
            sectors.append(None)

    df['sector'] = sectors
    
    # Drop rows where we couldn't find a sector
    df_enriched = df.dropna(subset=['sector'])
    
    # Save the new, complete dataset
    output_path = "nse_stocks_enriched.csv"
    df_enriched.to_csv(output_path, index=False)
    
    logging.info(f"Enrichment complete. Saved {len(df_enriched)} stocks with sector data to {output_path}")

if __name__ == "__main__":
    enrich_stock_data()