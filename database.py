# database.py
import sqlite3
import logging
from datetime import datetime
import pandas as pd
from config import DB_FILE

def initialize_db():
    """Creates the database and ensures the schema is up-to-date."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL, article_title TEXT NOT NULL,
            link TEXT, company_name TEXT NOT NULL, ticker TEXT NOT NULL, sentiment TEXT NOT NULL,
            confidence REAL NOT NULL, event_type TEXT, impact_score REAL, key_figures TEXT
        )
    ''')
    table_info = cursor.execute("PRAGMA table_info(insights)").fetchall()
    column_names = [info[1] for info in table_info]
    if 'link' not in column_names:
        cursor.execute("ALTER TABLE insights ADD COLUMN link TEXT")
    conn.commit()
    conn.close()

def save_specific_insight(article_title, link, company_name, ticker, sentiment_result, event_type, impact_score, key_figures_json):
    """Saves a single, fully enriched insight into the database."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO insights (timestamp, article_title, link, company_name, ticker, sentiment, confidence, event_type, impact_score, key_figures)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (datetime.now().isoformat(), article_title, link, company_name, ticker, 
              sentiment_result.get('sentiment', 'Neutral'), sentiment_result.get('confidence', 0.0), 
              event_type, impact_score, key_figures_json))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Error saving insight: {e}", exc_info=True)

def get_historical_sentiment(ticker: str):
    """Fetches all historical sentiment data for a specific ticker."""
    conn = sqlite3.connect(DB_FILE)
    query = "SELECT * FROM insights WHERE ticker = ? ORDER BY timestamp DESC"
    df = pd.read_sql_query(query, conn, params=(ticker,))
    conn.close()
    return df
