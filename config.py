# config.py

# --- SCHEDULER CONFIG ---
RUN_INTERVAL_SECONDS = 900  # 15 minutes
FEEDS_TO_PROCESS = {
    "Moneycontrol": {'url': "https://www.moneycontrol.com/rss/MCtopnews.xml", 'weight': 1.0},
    "ET Markets":   {'url': "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms", 'weight': 1.0},
    "Livemint":     {'url': "https://www.livemint.com/rss/companies", 'weight': 0.9},
}

# --- NLP PROCESSOR CONFIG ---
FUZZY_MATCH_THRESHOLD = 90
ENTITY_BLOCKLIST = {
    'swiggy', 'zerodha', 'byju\'s', 'razorpay', 'cred', 'phonepe', 'ola', 'oyo',
    'reserve bank of india', 'rbi', 'sebi', 'ministry of finance', 'flipkart'
}

# --- INFERENCE ENGINE CONFIG ---
GROQ_MODEL = "llama-3.1-8b-instant"
EVENT_IMPACT_MULTIPLIERS = {
    "Merger or Acquisition": 1.5, 
    "Earnings Report": 1.4, 
    "Legal or Regulatory Issue": 1.3
}
COMPETITIVE_KEYWORDS = {'beats', 'wins', 'outperforms', 'loses to', 'rival'}

# --- BACKTESTER CONFIG ---
TRANSACTION_COST_PERCENT = 0.2
BENCHMARK_TICKER = "^NSEI" # Nifty 50 Index
RISK_FREE_RATE = 0.07 # Assume a 7% annual risk-free rate for India