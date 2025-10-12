# database.py
import sqlite3
import logging
from datetime import datetime
import pandas as pd

DB_FILE = "insights.db"

def initialize_db():
    """Creates the database and the insights table if they don't exist."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # This SQL command creates our table with specific columns
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                article_title TEXT NOT NULL,
                company_name TEXT NOT NULL,
                ticker TEXT NOT NULL,
                sentiment TEXT NOT NULL,
                confidence REAL NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
        logging.info("Database initialized successfully.")
    except Exception as e:
        logging.error(f"Error initializing database: {e}")

def save_insight(article_title, tickers, sentiment_result):
    """Saves a generated insight into the SQLite database."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        sentiment = sentiment_result.get('sentiment', 'Neutral')
        confidence = sentiment_result.get('confidence', 0.0)
        
        # Save an entry for each company found in the article
        for company, ticker in tickers.items():
            cursor.execute('''
                INSERT INTO insights (timestamp, article_title, company_name, ticker, sentiment, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (timestamp, article_title, company, ticker, sentiment, confidence))
        
        conn.commit()
        conn.close()
        logging.info(f"Saved insight for tickers {list(tickers.values())} to database.")
    except Exception as e:
        logging.error(f"Error saving insight to database: {e}")


    # Add this function to the end of database.py

def get_historical_sentiment(ticker: str):
    """Fetches all historical sentiment data for a specific ticker."""
    try:
        conn = sqlite3.connect(DB_FILE)
        query = "SELECT timestamp, sentiment, confidence, article_title FROM insights WHERE ticker = ? ORDER BY timestamp DESC"
        # Use pandas to directly query the DB and get a DataFrame
        df = pd.read_sql_query(query, conn, params=(ticker,))
        conn.close()
        
        if not df.empty:
            # Convert timestamp string to datetime objects for plotting
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        return df
    except Exception as e:
        logging.error(f"Error fetching historical data for {ticker}: {e}")
        return pd.DataFrame() # Return an empty DataFrame on error