# tests/test_stock_data.py
"""Unit tests for stock_data.py — TTLCache and StockDataFetcher with mocked yfinance."""

import sys
import os
import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from stock_data import _TTLCache, StockDataFetcher


# ---------------------------------------------------------------------------
# _TTLCache
# ---------------------------------------------------------------------------

class TestTTLCache:
    def test_miss_on_empty_cache(self):
        cache = _TTLCache(ttl_seconds=300)
        assert cache.get("missing_key") is None

    def test_set_and_get(self):
        cache = _TTLCache(ttl_seconds=300)
        cache.set("key", {"price": 100})
        assert cache.get("key") == {"price": 100}

    def test_expired_entry_returns_none(self):
        cache = _TTLCache(ttl_seconds=1)
        past = datetime.now() - timedelta(seconds=10)
        cache._store["stale"] = {"data": "old", "ts": past}
        assert cache.get("stale") is None

    def test_overwrite_existing_key(self):
        cache = _TTLCache(ttl_seconds=300)
        cache.set("k", "v1")
        cache.set("k", "v2")
        assert cache.get("k") == "v2"


# ---------------------------------------------------------------------------
# StockDataFetcher — mocked yfinance
# ---------------------------------------------------------------------------

def _make_fake_hist(prices=None):
    """Return a minimal DataFrame mimicking yfinance history output.
    The index MUST be named 'Date' — yfinance always names it this way and
    StockDataFetcher.get_historical_data() relies on it after reset_index().
    """
    prices = prices or [2800.0, 2850.0]
    dates = pd.date_range(end=pd.Timestamp.today(), periods=len(prices), freq="B", name="Date")
    return pd.DataFrame({
        "Close": prices,
        "High": [p + 20 for p in prices],
        "Low": [p - 20 for p in prices],
        "Volume": [5_000_000] * len(prices),
    }, index=dates)


class TestStockDataFetcher:
    @pytest.fixture(autouse=True)
    def setup(self):
        # Each test gets a fresh fetcher with a clean cache
        self.fetcher = StockDataFetcher()
        self.fetcher._cache = _TTLCache(ttl_seconds=300)

    def _mock_ticker(self, hist_df):
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = hist_df
        mock_ticker.info = {
            "marketCap": 1_900_000_000_000,
            "trailingPE": 28.5,
            "fiftyTwoWeekHigh": 3050.0,
            "fiftyTwoWeekLow": 2200.0,
        }
        return mock_ticker

    def test_get_stock_price_returns_dict(self):
        with patch("yfinance.Ticker", return_value=self._mock_ticker(_make_fake_hist())):
            result = self.fetcher.get_stock_price("RELIANCE")
        assert isinstance(result, dict)

    def test_get_stock_price_has_required_keys(self):
        with patch("yfinance.Ticker", return_value=self._mock_ticker(_make_fake_hist())):
            result = self.fetcher.get_stock_price("RELIANCE")
        for key in ("current_price", "change", "change_percent", "volume"):
            assert key in result

    def test_get_stock_price_change_calculated_correctly(self):
        hist = _make_fake_hist([2800.0, 2850.0])
        with patch("yfinance.Ticker", return_value=self._mock_ticker(hist)):
            result = self.fetcher.get_stock_price("RELIANCE")
        assert result["change"] == pytest.approx(50.0, abs=0.01)
        assert result["change_percent"] == pytest.approx(1.786, abs=0.01)

    def test_empty_history_returns_none(self):
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame()
        mock_ticker.info = {}
        with patch("yfinance.Ticker", return_value=mock_ticker):
            result = self.fetcher.get_stock_price("FAKE")
        assert result is None

    def test_result_is_cached_on_second_call(self):
        with patch("yfinance.Ticker", return_value=self._mock_ticker(_make_fake_hist())) as mock_yf:
            self.fetcher.get_stock_price("RELIANCE")
            self.fetcher.get_stock_price("RELIANCE")
        # yfinance.Ticker should be called only once — second call hits cache
        assert mock_yf.call_count == 1

    def test_get_historical_data_returns_dataframe(self):
        hist = _make_fake_hist([2800, 2810, 2820, 2830, 2840])
        with patch("yfinance.Ticker", return_value=self._mock_ticker(hist)):
            result = self.fetcher.get_historical_data("RELIANCE", period="5d")
        assert isinstance(result, pd.DataFrame)
        assert "Close" in result.columns

    def test_get_multiple_stocks(self):
        with patch("yfinance.Ticker", return_value=self._mock_ticker(_make_fake_hist())):
            result = self.fetcher.get_multiple_stocks({"Reliance": "RELIANCE"})
        assert "Reliance" in result
