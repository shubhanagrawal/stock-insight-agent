# database.py
import os
import logging
import pandas as pd
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# --- Connection Pooling: The Professional Standard ---
# This creates a pool of reusable connections, which is far more efficient
# than opening a new one for every single query.
try:
    connection_pool = psycopg2.pool.SimpleConnectionPool(
        1, 10, # min/max connections
        host=DB_HOST, port=DB_PORT, user=DB_USER,
        password=DB_PASSWORD, dbname=DB_NAME
    )
    logging.info("PostgreSQL connection pool created successfully.")
except Exception as e:
    logging.error(f"Failed to create PostgreSQL connection pool: {e}")
    connection_pool = None

def get_db_connection():
    """Gets a connection from the pool."""
    if connection_pool:
        return connection_pool.getconn()
    raise ConnectionError("Database connection pool is not available.")

def release_db_connection(conn):
    """Returns a connection to the pool."""
    if connection_pool:
        connection_pool.putconn(conn)

def initialize_db():
    """Creates the 'insights' table in PostgreSQL if it doesn't exist."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Note the data type changes for PostgreSQL (SERIAL, TIMESTAMPTZ, JSONB)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS insights (
                    id SERIAL PRIMARY KEY, timestamp TIMESTAMPTZ NOT NULL,
                    article_title TEXT NOT NULL, link TEXT, company_name TEXT NOT NULL,
                    ticker TEXT NOT NULL, sentiment TEXT NOT NULL, confidence REAL NOT NULL,
                    event_type TEXT, impact_score REAL, key_figures JSONB
                );
            ''')
            conn.commit()
        logging.info("PostgreSQL database initialized successfully.")
    finally:
        release_db_connection(conn)

def save_specific_insight(article_title, link, company_name, ticker, sentiment_result, event_type, impact_score, key_figures_json):
    """Saves a single, enriched insight into the PostgreSQL database."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # PostgreSQL uses %s for placeholders, not ?
            cursor.execute('''
                INSERT INTO insights (timestamp, article_title, link, company_name, ticker, sentiment, confidence, event_type, impact_score, key_figures)
                VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (article_title, link, company_name, ticker, 
                  sentiment_result.get('sentiment', 'Neutral'), sentiment_result.get('confidence', 0.0), 
                  event_type, impact_score, key_figures_json))
            conn.commit()
    finally:
        release_db_connection(conn)

def get_historical_sentiment(ticker: str):
    """Fetches historical sentiment data for a specific ticker from PostgreSQL."""
    conn = get_db_connection()
    try:
        query = "SELECT * FROM insights WHERE ticker = %s ORDER BY timestamp DESC"
        df = pd.read_sql_query(query, conn, params=(ticker,))
        return df
    finally:
        release_db_connection(conn)