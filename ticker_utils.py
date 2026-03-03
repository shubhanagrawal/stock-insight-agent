# ticker_utils.py
"""
NSE ticker map loader: returns {company_name: ticker_symbol}.

Load strategy (in order):
  1. PostgreSQL via the shared connection pool in database.py
  2. nse_stocks_enriched.csv  (local, broader dataset)
  3. nse_stocks.csv           (local, raw NSE listing)

This means the app runs correctly even when the database is unreachable
(e.g. local dev, CI, Supabase paused) — it just falls back to the CSV.
"""

import os
import logging
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

_DIR = os.path.dirname(__file__)
_ENRICHED_CSV = os.path.join(_DIR, "nse_stocks_enriched.csv")
_RAW_CSV      = os.path.join(_DIR, "nse_stocks.csv")


def _load_from_db() -> dict:
    """Try loading from PostgreSQL via the shared pool. Returns {} on any failure."""
    try:
        from database import get_db_connection, release_db_connection, connection_pool
        if not connection_pool:
            return {}
        conn = get_db_connection()
        try:
            df = pd.read_sql_query("SELECT name, ticker FROM stocks", conn)
            if df.empty:
                return {}
            ticker_map = dict(zip(df["name"].str.strip(), df["ticker"].str.strip()))
            logging.info(f"Loaded {len(ticker_map)} tickers from PostgreSQL.")
            return ticker_map
        finally:
            release_db_connection(conn)
    except Exception as e:
        logging.warning(f"DB ticker load skipped: {e}")
        return {}


def _load_from_csv(csv_path: str) -> dict:
    """Load ticker map from an NSE CSV file. Returns {} on any failure."""
    try:
        df = pd.read_csv(csv_path)
        # NSE CSVs have inconsistent spacing in headers — normalise them
        df.columns = df.columns.str.strip().str.upper()

        name_col = next((c for c in df.columns if "NAME" in c), None)
        sym_col  = next((c for c in df.columns if "SYMBOL" in c), None)

        if not name_col or not sym_col:
            logging.error(f"Expected NAME and SYMBOL columns in {csv_path}. Got: {list(df.columns)}")
            return {}

        df = df[[name_col, sym_col]].dropna()
        df[name_col] = df[name_col].str.strip()
        df[sym_col]  = df[sym_col].str.strip()

        ticker_map = dict(zip(df[name_col], df[sym_col]))
        logging.info(f"Loaded {len(ticker_map)} tickers from {os.path.basename(csv_path)}.")
        return ticker_map

    except Exception as e:
        logging.error(f"Failed to read {csv_path}: {e}")
        return {}


def load_nse_tickers() -> dict:
    """Return {company_name: ticker_symbol} from the best available source."""
    # 1 — PostgreSQL
    result = _load_from_db()
    if result:
        return result

    # 2 — Enriched CSV (has sector/industry metadata as well)
    result = _load_from_csv(_ENRICHED_CSV)
    if result:
        return result

    # 3 — Raw NSE listing CSV
    result = _load_from_csv(_RAW_CSV)
    if result:
        return result

    logging.error(
        "Could not load NSE tickers from any source. "
        "Ensure nse_stocks.csv is present or the database is reachable."
    )
    return {}