# tests/conftest.py
"""Shared pytest fixtures for the stock-insight-agent test suite."""

import pytest


# ---------------------------------------------------------------------------
# Ticker / NSE map fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_nse_map():
    """Small in-memory NSE ticker map — avoids CSV / DB loading."""
    return {
        "Reliance Industries Limited": "RELIANCE",
        "Infosys Limited": "INFY",
        "HDFC Bank Limited": "HDFCBANK",
        "State Bank of India": "SBIN",
        "Tata Consultancy Services Limited": "TCS",
        "IDFC First Bank Limited": "IDFCFIRSTB",
        "Wipro Limited": "WIPRO",
    }


# ---------------------------------------------------------------------------
# Sentiment fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sentiment_positive():
    return {"sentiment": "Positive", "confidence": 0.9}


@pytest.fixture
def sentiment_negative():
    return {"sentiment": "Negative", "confidence": 0.85}


@pytest.fixture
def sentiment_neutral():
    return {"sentiment": "Neutral", "confidence": 0.5}


# ---------------------------------------------------------------------------
# Stock data fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_stock_price_data():
    return {
        "ticker": "RELIANCE",
        "current_price": 2850.50,
        "previous_close": 2820.00,
        "change": 30.50,
        "change_percent": 1.08,
        "volume": 5_000_000,
        "market_cap": 1_900_000_000_000,
        "pe_ratio": 28.5,
        "day_high": 2860.00,
        "day_low": 2810.00,
        "fifty_two_week_high": 3050.00,
        "fifty_two_week_low": 2200.00,
    }


# ---------------------------------------------------------------------------
# Article / insight fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_linked_tickers():
    return {
        "Reliance Industries Limited": {
            "ticker": "RELIANCE",
            "ner_name": "Reliance",
            "score": 95,
        }
    }


@pytest.fixture
def sample_article():
    return {
        "title": "Reliance posts record quarterly profit",
        "content": (
            "Reliance Industries reported a record quarterly profit of ₹20,000 crore, "
            "up 18% year-on-year. Revenue also rose 12% driven by Jio and retail segments."
        ),
        "link": "https://example.com/reliance-profit",
    }
