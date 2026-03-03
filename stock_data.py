import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import logging

# NSE suffix for Indian stocks
NSE_SUFFIX = ".NS"
BSE_SUFFIX = ".BO"

# ── Sentiment strategy note ──────────────────────────────────────────────────
# This project uses TWO sentiment paths intentionally:
#   • Groq LLM (core_nlp.py)         → used by worker.py / app.py pipeline
#     High accuracy, slower, costs API calls. Used for batch news processing.
#   • TextBlob + keywords (advanced_analysis.py) → used by dashboard.py
#     Fast, free, no API call. Used for real-time interactive dashboard UI.
# ─────────────────────────────────────────────────────────────────────────────

class _TTLCache:
    """Lightweight in-process TTL cache to avoid repeated yfinance API calls."""
    def __init__(self, ttl_seconds: int = 300):
        self._store: dict = {}
        self._ttl = ttl_seconds

    def get(self, key):
        entry = self._store.get(key)
        if entry and (datetime.now() - entry['ts']).seconds < self._ttl:
            return entry['data']
        return None

    def set(self, key, data):
        self._store[key] = {'data': data, 'ts': datetime.now()}

_cache = _TTLCache(ttl_seconds=300)

class StockDataFetcher:
    def __init__(self):
        self._cache = _cache  # shared module-level TTL cache
    
    def get_stock_price(self, ticker, exchange="NSE"):
        """Get current stock price and basic metrics"""
        try:
            # Add exchange suffix
            if exchange == "NSE":
                full_ticker = f"{ticker}{NSE_SUFFIX}"
            else:
                full_ticker = f"{ticker}{BSE_SUFFIX}"
            
            cache_key = f"{full_ticker}_price"
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached
            
            # Fetch data
            stock = yf.Ticker(full_ticker)
            info = stock.info
            hist = stock.history(period="2d")
            
            if hist.empty:
                return None
            
            current_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
            change = current_price - prev_price
            change_percent = (change / prev_price) * 100 if prev_price != 0 else 0
            
            data = {
                'ticker': ticker,
                'current_price': round(current_price, 2),
                'previous_close': round(prev_price, 2),
                'change': round(change, 2),
                'change_percent': round(change_percent, 2),
                'volume': hist['Volume'].iloc[-1] if 'Volume' in hist else 0,
                'market_cap': info.get('marketCap', 'N/A'),
                'pe_ratio': info.get('trailingPE', 'N/A'),
                'day_high': round(hist['High'].iloc[-1], 2),
                'day_low': round(hist['Low'].iloc[-1], 2),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 'N/A'),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow', 'N/A'),
            }
            
            self._cache.set(cache_key, data)
            return data
            
        except Exception as e:
            logging.error(f"Error fetching stock data for {ticker}: {e}")
            return None
    
    def get_historical_data(self, ticker, period="1mo", exchange="NSE"):
        """Get historical stock data"""
        try:
            full_ticker = f"{ticker}{NSE_SUFFIX if exchange == 'NSE' else BSE_SUFFIX}"
            
            cache_key = f"{full_ticker}_hist_{period}"
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached
            
            stock = yf.Ticker(full_ticker)
            hist = stock.history(period=period)
            
            if hist.empty:
                return None
            
            # Convert to format suitable for plotting
            hist.reset_index(inplace=True)
            hist['Date'] = hist['Date'].dt.strftime('%Y-%m-%d')
            
            self._cache.set(cache_key, hist)
            return hist
            
        except Exception as e:
            logging.error(f"Error fetching historical data for {ticker}: {e}")
            return None
    
    def get_technical_indicators(self, ticker, period="3mo", exchange="NSE"):
        """Calculate basic technical indicators"""
        try:
            hist = self.get_historical_data(ticker, period, exchange)
            if hist is None:
                return None
            
            # Calculate moving averages
            hist['MA_20'] = hist['Close'].rolling(window=20).mean()
            hist['MA_50'] = hist['Close'].rolling(window=50).mean()
            
            # Calculate RSI
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            hist['RSI'] = 100 - (100 / (1 + rs))
            
            # Calculate Bollinger Bands
            hist['BB_Middle'] = hist['Close'].rolling(window=20).mean()
            bb_std = hist['Close'].rolling(window=20).std()
            hist['BB_Upper'] = hist['BB_Middle'] + (bb_std * 2)
            hist['BB_Lower'] = hist['BB_Middle'] - (bb_std * 2)
            
            return hist
            
        except Exception as e:
            logging.error(f"Error calculating technical indicators for {ticker}: {e}")
            return None
    
    def get_multiple_stocks(self, tickers_dict, exchange="NSE"):
        """Get data for multiple stocks"""
        results = {}
        for company, ticker in tickers_dict.items():
            data = self.get_stock_price(ticker, exchange)
            if data:
                results[company] = data
        return results
    
    # _is_cached and _cache_data removed — now handled by the shared _TTLCache above.

# Alternative free API option (Alpha Vantage)
class AlphaVantageStockData:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
    
    def get_stock_quote(self, symbol):
        """Get real-time stock quote"""
        try:
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': f'{symbol}.BSE',  # Try BSE first
                'apikey': self.api_key
            }
            
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
            if 'Global Quote' in data:
                quote = data['Global Quote']
                return {
                    'symbol': symbol,
                    'price': float(quote['05. price']),
                    'change': float(quote['09. change']),
                    'change_percent': quote['10. change percent'].replace('%', ''),
                    'volume': int(quote['06. volume']) if quote['06. volume'] != '0' else 0,
                    'high': float(quote['03. high']),
                    'low': float(quote['04. low'])
                }
            
            return None
            
        except Exception as e:
            logging.error(f"Error fetching from Alpha Vantage: {e}")
            return None

# Enhanced insight generation with stock price context
def generate_enhanced_insight(article_title, tickers_dict, sentiment, stock_fetcher):
    """Generate insight with real-time stock price context"""
    if not tickers_dict:
        return "No insights generated as no tickers were found."
    
    primary_company = list(tickers_dict.keys())[0]
    primary_ticker = tickers_dict[primary_company]
    
    # Get stock data
    stock_data = stock_fetcher.get_stock_price(primary_ticker)
    
    # Enhanced rationale with stock context
    if sentiment == "Positive":
        base_rationale = "The news appears positive, suggesting favorable events or results for the company."
    elif sentiment == "Negative":
        base_rationale = "The news appears negative, indicating potential challenges or poor performance."
    else:
        base_rationale = "The news is neutral, likely a factual report without strong sentiment."
    
    # Add stock context if available
    stock_context = ""
    if stock_data:
        price = stock_data['current_price']
        change = stock_data['change']
        change_pct = stock_data['change_percent']
        
        direction = "📈" if change > 0 else "📉" if change < 0 else "➡️"
        stock_context = f"""
    - **Current Price:** ₹{price} ({direction} {change:+.2f}, {change_pct:+.2f}%)
    - **Day Range:** ₹{stock_data['day_low']} - ₹{stock_data['day_high']}
    - **Volume:** {stock_data['volume']:,}"""
        
        if stock_data['pe_ratio'] != 'N/A':
            stock_context += f"\n    - **P/E Ratio:** {stock_data['pe_ratio']:.2f}"
    
    insight_card = f"""
    ---
    💡 **Enhanced Market Insight**
    ---
    - **Company:** {primary_company} ({primary_ticker})
    - **Sentiment Impact:** {sentiment}
    - **News Source:** "{article_title}"{stock_context}
    - **Analysis:** {base_rationale}
    """
    
    return insight_card.strip()