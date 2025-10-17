import sqlite3
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import logging

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
DB_FILE = "insights.db"
TRANSACTION_COST_PERCENT = 0.2
BENCHMARK_TICKER = "^NSEI" # Nifty 50 Index

# In backtester.py

def run_backtest():
    """
    Performs a rigorous backtest by measuring Alpha, with robust data handling
    for both the stock and the benchmark index.
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
        logging.warning("No insights old enough to backtest were found.")
        return

    correct_predictions, total_predictions, results = 0, 0, []

    for index, row in df.iterrows():
        ticker, prediction_date_str, sentiment = row['ticker'], row['timestamp'], row['sentiment']
        if sentiment == 'Neutral': continue

        prediction_date = pd.to_datetime(prediction_date_str).date()
        yahoo_ticker = f"{ticker}.NS"
        try:
            start_date = prediction_date - timedelta(days=5)
            end_date = prediction_date + timedelta(days=5)
            
            stock_data = yf.download(yahoo_ticker, start=start_date, end=end_date, progress=False)
            benchmark_data = yf.download(BENCHMARK_TICKER, start=start_date, end=end_date, progress=False)

            if stock_data.empty or benchmark_data.empty: continue

            actual_prediction_date = stock_data.index.asof(pd.to_datetime(prediction_date))
            if pd.isna(actual_prediction_date): continue
            
            prediction_day_index = stock_data.index.get_loc(actual_prediction_date)
            if prediction_day_index == 0 or prediction_day_index >= len(stock_data) - 1: continue

            # --- ROBUST DATA SELECTION FOR BOTH STOCK AND BENCHMARK ---
            stock_close_series = stock_data['Close']
            if isinstance(stock_close_series, pd.DataFrame):
                stock_close_series = stock_close_series.iloc[:, 0]
            
            benchmark_close_series = benchmark_data['Close']
            if isinstance(benchmark_close_series, pd.DataFrame):
                benchmark_close_series = benchmark_close_series.iloc[:, 0]
            # -----------------------------------------------------------

            stock_prev_close = stock_close_series.iloc[prediction_day_index - 1]
            stock_next_close = stock_close_series.iloc[prediction_day_index + 1]
            stock_return = ((stock_next_close - stock_prev_close) / stock_prev_close) * 100

            benchmark_prev_close = benchmark_close_series.asof(stock_data.index[prediction_day_index - 1])
            benchmark_next_close = benchmark_close_series.asof(stock_data.index[prediction_day_index + 1])
            
            if pd.isna(benchmark_prev_close) or pd.isna(benchmark_next_close) or benchmark_prev_close == 0:
                continue

            benchmark_return = ((benchmark_next_close - benchmark_prev_close) / benchmark_prev_close) * 100
            
            alpha = stock_return - benchmark_return
            net_alpha = alpha - TRANSACTION_COST_PERCENT

            actual_movement = "Positive" if net_alpha > 0 else "Negative"
            is_correct = (sentiment == actual_movement)

            if is_correct: correct_predictions += 1
            total_predictions += 1
            results.append([ticker, prediction_date, sentiment, f"{net_alpha:.2f}%", is_correct])

        except Exception as e:
            logging.error(f"Could not process backtest for ticker {ticker}: {e}", exc_info=True)

    # --- Display Final Report (unchanged) ---
    print("\n" + "="*60)
    print("              ALPHA BACKTESTING REPORT")
    print("="*60)
    if total_predictions > 0:
        report_df = pd.DataFrame(results, columns=["Ticker", "Date", "Prediction", "Net Alpha", "Correct?"])
        print(report_df.to_string())
        accuracy = (correct_predictions / total_predictions) * 100
        print(f"\nOverall Accuracy (Based on Alpha): {accuracy:.2f}% ({correct_predictions} correct out of {total_predictions})")
    else:
        print("No actionable (Positive/Negative) insights were found to evaluate.")

if __name__ == "__main__":
    run_backtest()