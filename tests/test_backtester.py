# tests/test_backtester.py
"""Unit tests for backtester.py — mocked DB and yfinance, no real connections."""

import sys
import os
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_insights_df(rows=None):
    """Fake database query result with insight rows."""
    if rows is None:
        rows = [
            {
                "ticker": "RELIANCE",
                "timestamp": pd.Timestamp("2025-12-01"),
                "sentiment": "Positive",
            },
            {
                "ticker": "INFY",
                "timestamp": pd.Timestamp("2025-12-02"),
                "sentiment": "Negative",
            },
        ]
    return pd.DataFrame(rows)


def _make_price_history(start_price=100.0, days=10, drift=1.0):
    """Simulate yfinance price history around a prediction date."""
    dates = pd.date_range("2025-11-25", periods=days, freq="B")
    prices = [start_price + i * drift for i in range(days)]
    return pd.DataFrame({"Close": prices}, index=dates)


# ---------------------------------------------------------------------------
# run_backtest — DB unavailable path
# ---------------------------------------------------------------------------

class TestRunBacktestNoDB:
    def test_exits_gracefully_when_no_pool(self, caplog):
        """Should log an error and return immediately — no crash."""
        import logging
        with patch("backtester.connection_pool", None):
            from backtester import run_backtest
            with caplog.at_level(logging.ERROR):
                run_backtest()
        assert any("Backtest aborted" in r.message for r in caplog.records)

    def test_exits_cleanly_when_db_query_fails(self):
        """DB is available but the query throws — should return without crashing."""
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_pool.getconn.return_value = mock_conn

        with (
            patch("backtester.connection_pool", mock_pool),
            patch("backtester.get_db_connection", side_effect=Exception("DB error")),
        ):
            from backtester import run_backtest
            run_backtest()   # Should not raise


# ---------------------------------------------------------------------------
# run_backtest — happy path with full mocks
# ---------------------------------------------------------------------------

class TestRunBacktestHappyPath:
    def _patch_backtest(self, insights_df, stock_hist, bench_hist):
        """Context manager stack that patches all external calls."""
        import contextlib

        mock_conn = MagicMock()
        mock_pool = MagicMock()

        patches = [
            patch("backtester.connection_pool", mock_pool),
            patch("backtester.get_db_connection", return_value=mock_conn),
            patch("backtester.release_db_connection"),
            patch("pandas.read_sql_query", return_value=insights_df),
            patch(
                "yfinance.download",
                side_effect=[stock_hist, bench_hist] * 10,  # alternating stock/bench
            ),
        ]
        return contextlib.ExitStack(), patches

    def test_runs_without_error_on_valid_data(self, capsys):
        mock_conn = MagicMock()
        stock_hist = _make_price_history(100, 10, 1.0)
        bench_hist = _make_price_history(200, 10, 0.5)
        insights = _make_insights_df()

        with (
            patch("backtester.connection_pool", MagicMock()),
            patch("backtester.get_db_connection", return_value=mock_conn),
            patch("backtester.release_db_connection"),
            patch("pandas.read_sql_query", return_value=insights),
            patch("yfinance.download", side_effect=[stock_hist, bench_hist] * 5),
        ):
            from backtester import run_backtest
            run_backtest()   # should not raise

        out = capsys.readouterr().out
        assert "BACKTESTING REPORT" in out

    def test_empty_insights_prints_no_results_message(self, caplog):
        import logging
        mock_conn = MagicMock()
        with (
            patch("backtester.connection_pool", MagicMock()),
            patch("backtester.get_db_connection", return_value=mock_conn),
            patch("backtester.release_db_connection"),
            patch("pandas.read_sql_query", return_value=pd.DataFrame()),
        ):
            from backtester import run_backtest
            with caplog.at_level(logging.WARNING):
                run_backtest()

        # Early return logs a warning — no stdout print is produced
        assert any("No actionable insights" in r.message for r in caplog.records)
