# backtester.py
import sqlite3
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import logging

# Configure logging for a clean report
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

DB_FILE = "insights.db"

# In your backtester.py file

def run_backtest():
    """
    Performs a backtest of the sentiment predictions stored in the database.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        three_days_ago = (datetime.now() - timedelta(days=3)).isoformat()
        query = "SELECT * FROM insights WHERE timestamp < ?"
        df = pd.read_sql_query(query, conn, params=(three_days_ago,))
        conn.close()
    except Exception as e:
        logging.error(f"Could not read from database: {e}")
        return

    if df.empty:
        logging.warning("No insights older than 3 days were found to backtest. Collect more data over time.")
        return

    logging.info(f"Loaded {len(df)} insights for backtesting.")

    correct_predictions = 0
    total_predictions = 0
    results = []

    for index, row in df.iterrows():
        ticker = row['ticker']
        prediction_date = datetime.fromisoformat(row['timestamp']).date()
        sentiment = row['sentiment']

        if sentiment == 'Neutral':
            continue

        yahoo_ticker = f"{ticker}.NS"
        
        try:
            start_date = prediction_date
            end_date = start_date + timedelta(days=5)
            stock_data = yf.download(yahoo_ticker, start=start_date, end=end_date, progress=False)
            
            if len(stock_data) < 2:
                logging.warning(f"Not enough historical data for {ticker} on {prediction_date}")
                continue

            # --- FIX APPLIED HERE ---
            # This robustly handles cases where yfinance returns duplicate columns.
            open_prices = stock_data['Open']
            if isinstance(open_prices, pd.DataFrame):
                # If we get a DataFrame, use the first column by position
                next_day_open = open_prices.iloc[1, 0]
            else: # It's a Series, as normally expected
                next_day_open = open_prices.iloc[1]

            close_prices = stock_data['Close']
            if isinstance(close_prices, pd.DataFrame):
                next_day_close = close_prices.iloc[1, 0]
            else:
                next_day_close = close_prices.iloc[1]
            # --------------------------
            
            # Ensure we have valid numbers before calculating
            if pd.isna(next_day_open) or pd.isna(next_day_close) or next_day_open == 0:
                logging.warning(f"Missing price data for {ticker} on the next trading day.")
                continue

            daily_return = ((next_day_close - next_day_open) / next_day_open) * 100
            actual_movement = "Positive" if daily_return > 0 else "Negative"
            is_correct = (sentiment == actual_movement)

            if is_correct:
                correct_predictions += 1
            
            total_predictions += 1
            results.append([ticker, prediction_date, sentiment, f"{daily_return:.2f}%", is_correct])

        except Exception as e:
            logging.error(f"Could not process ticker {ticker}: {e}")

    # The report section remains the same
    print("\n" + "="*60)
    print("              SENTIMENT AGENT BACKTESTING REPORT")
    print("="*60)

    if total_predictions > 0:
        report_df = pd.DataFrame(results, columns=["Ticker", "Date", "Prediction", "Next Day Return", "Correct?"])
        print(report_df.to_string())
        
        accuracy = (correct_predictions / total_predictions) * 100
        print("\n" + "-"*60)
        print(f"Overall Accuracy: {accuracy:.2f}% ({correct_predictions} correct out of {total_predictions})")
        print("-" * 60)
    else:
        print("No actionable (Positive/Negative) insights older than 3 days were found to evaluate.")
# --- THIS IS THE CRITICAL PART THAT WAS MISSING ---
if __name__ == "__main__":
    run_backtest()
# --------------------------------------------------