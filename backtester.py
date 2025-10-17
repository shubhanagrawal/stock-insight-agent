import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import logging
import numpy as np
from scipy.stats import binomtest

# --- Correctly import the PostgreSQL connection functions ---
from database import get_db_connection, release_db_connection
from config import TRANSACTION_COST_PERCENT, BENCHMARK_TICKER, RISK_FREE_RATE

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def run_backtest():
    """
    Performs a rigorous backtest by reading from the production PostgreSQL database,
    measuring Alpha, p-value, and Sharpe Ratio.
    """
    conn = None # Initialize conn to None
    try:
        # --- FIX: Use the PostgreSQL connection pool ---
        conn = get_db_connection()
        query = "SELECT * FROM insights WHERE sentiment != 'Neutral' AND timestamp < NOW() - INTERVAL '3 days'"
        df = pd.read_sql_query(query, conn)
        # ---------------------------------------------

    except Exception as e:
        logging.error(f"Could not read from PostgreSQL database: {e}")
        return
    finally:
        if conn:
            release_db_connection(conn)

    if df.empty:
        logging.warning("No actionable insights old enough were found in the database to backtest.")
        return

    correct_predictions, total_predictions, results = 0, 0, []
    net_alpha_returns = []

    for index, row in df.iterrows():
        ticker, prediction_date, sentiment = row['ticker'], row['timestamp'].date(), row['sentiment']
        
        yahoo_ticker = f"{ticker}.NS"
        try:
            # --- Data Fetching and Alignment (unchanged) ---
            start_date, end_date = prediction_date - timedelta(days=5), prediction_date + timedelta(days=5)
            stock_data = yf.download(yahoo_ticker, start=start_date, end=end_date, progress=False, auto_adjust=True)
            benchmark_data = yf.download(BENCHMARK_TICKER, start=start_date, end=end_date, progress=False, auto_adjust=True)
            if stock_data.empty or benchmark_data.empty: continue

            actual_prediction_date = stock_data.index.asof(pd.to_datetime(prediction_date))
            if pd.isna(actual_prediction_date): continue
            
            prediction_day_index = stock_data.index.get_loc(actual_prediction_date)
            if prediction_day_index == 0 or prediction_day_index >= len(stock_data) - 1: continue

            # --- Alpha Calculation (unchanged) ---
            stock_close_series = stock_data['Close'].iloc[:, 0] if isinstance(stock_data['Close'], pd.DataFrame) else stock_data['Close']
            benchmark_close_series = benchmark_data['Close'].iloc[:, 0] if isinstance(benchmark_data['Close'], pd.DataFrame) else benchmark_data['Close']
            
            stock_prev_close = stock_close_series.iloc[prediction_day_index - 1]
            stock_next_close = stock_close_series.iloc[prediction_day_index + 1]
            stock_return = ((stock_next_close - stock_prev_close) / stock_prev_close) * 100

            benchmark_prev_close = benchmark_close_series.asof(stock_data.index[prediction_day_index - 1])
            benchmark_next_close = benchmark_close_series.asof(stock_data.index[prediction_day_index + 1])
            if pd.isna(benchmark_prev_close) or pd.isna(benchmark_next_close): continue
            benchmark_return = ((benchmark_next_close - benchmark_prev_close) / benchmark_prev_close) * 100
            
            alpha = stock_return - benchmark_return
            net_alpha = alpha - TRANSACTION_COST_PERCENT
            net_alpha_returns.append(net_alpha)

            is_correct = (sentiment == "Positive" and net_alpha > 0) or (sentiment == "Negative" and net_alpha < 0)

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
        print(report_df.to_string(index=False))
        
        accuracy = (correct_predictions / total_predictions) * 100
        
        p_value_result = binomtest(correct_predictions, n=total_predictions, p=0.5, alternative='greater')
        p_value = p_value_result.pvalue

        returns_array = np.array(net_alpha_returns) / 100
        daily_risk_free_rate = (1 + RISK_FREE_RATE)**(1/252) - 1
        excess_returns = returns_array - daily_risk_free_rate
        sharpe_ratio = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252) if np.std(excess_returns) > 0 else 0
        
        print("\n" + "-"*60)
        print("                STATISTICAL ANALYSIS")
        print("-" * 60)
        print(f"Overall Accuracy (Based on Alpha): {accuracy:.2f}% ({correct_predictions}/{total_predictions})")
        print(f"P-value (Probability of random luck): {p_value:.4f}")
        print(f"Annualized Sharpe Ratio: {sharpe_ratio:.2f}")
        
        if p_value < 0.05:
            print("\nConclusion: The result is STATISTICALLY SIGNIFICANT.")
        else:
            print("\nConclusion: Result is NOT statistically significant. More data is needed.")
        print("-" * 60)
    else:
        print("No actionable insights old enough were found to evaluate.")

if __name__ == "__main__":
    run_backtest()