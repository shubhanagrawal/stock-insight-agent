# ticker_mapping.py

# A dictionary to map company name variations to their official NSE ticker.
# We use lowercase for the keys to make matching case-insensitive.
COMPANY_TICKER_MAP = {
    # Grasim
    "grasim industries": "GRASIM.NS",
    "grasim": "GRASIM.NS",

    # Reliance
    "reliance industries": "RELIANCE.NS",
    "ril": "RELIANCE.NS",
    "reliance": "RELIANCE.NS",

    # Infosys
    "infosys": "INFY.NS",

    # HDFC Bank
    "hdfc bank": "HDFCBANK.NS",
    "hdfc": "HDFCBANK.NS",

    # Tata Consultancy Services
    "tata consultancy services": "TCS.NS",
    "tcs": "TCS.NS",
}