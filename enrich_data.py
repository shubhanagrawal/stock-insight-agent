import pandas as pd
import yfinance as yf
import logging
from time import sleep
from tqdm import tqdm
import requests
import psycopg2
import os
from dotenv import load_dotenv

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
load_dotenv()
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
NSE_URL = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"

def run_knowledge_base_update():
    """
    Downloads the latest stock list, enriches it with sector data, and
    upserts it into the production PostgreSQL database.
    """
    logging.info("--- Starting Knowledge Base Update ---")

    # 1. Download latest stock list
    try:
        response = requests.get(NSE_URL, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        with open("nse_stocks_temp.csv", "w", encoding='utf-8') as f:
            f.write(response.text)
        df = pd.read_csv("nse_stocks_temp.csv")
        df.columns = df.columns.str.strip()
    except Exception as e:
        logging.error(f"Failed to download from NSE: {e}"); return

    # 2. Enrich with Sector Data
    sectors = []
    for ticker_symbol in tqdm(df['SYMBOL'], desc="Enriching data"):
        try:
            ticker = yf.Ticker(f"{ticker_symbol}.NS")
            sector = ticker.info.get('sector')
            sectors.append(sector)
            sleep(0.1)
        except Exception:
            sectors.append(None)
    df['sector'] = sectors
    
    # 3. Clean and Prepare Data for Upsert
    df_enriched = df.dropna(subset=['sector', 'NAME OF COMPANY', 'SYMBOL'])
    records = df_enriched[['SYMBOL', 'NAME OF COMPANY', 'sector']].to_records(index=False)

    # 4. Upsert into PostgreSQL Database
    conn = None
    try:
        conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, dbname=DB_NAME)
        with conn.cursor() as cursor:
            # This query will INSERT new stocks or UPDATE existing ones if they change
            upsert_query = """
            INSERT INTO stocks (ticker, name, sector, last_updated)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (ticker) DO UPDATE SET
                name = EXCLUDED.name,
                sector = EXCLUDED.sector,
                last_updated = NOW();
            """
            cursor.executemany(upsert_query, records)
            conn.commit()
        logging.info(f"Successfully upserted {len(records)} stocks into the database.")
    except Exception as e:
        logging.error(f"Database upsert failed: {e}")
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    run_knowledge_base_update()