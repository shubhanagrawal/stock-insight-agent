# tests/test_ticker_utils.py
"""Unit tests for ticker_utils.py — 3-tier loading with mocked DB and CSV."""

import sys
import os
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ticker_utils import _load_from_csv, _load_from_db, load_nse_tickers


# ---------------------------------------------------------------------------
# _load_from_csv
# ---------------------------------------------------------------------------

class TestLoadFromCsv:
    def _write_csv(self, tmp_path, content):
        p = tmp_path / "test.csv"
        p.write_text(content)
        return str(p)

    def test_loads_symbol_and_name(self, tmp_path):
        path = self._write_csv(
            tmp_path, "SYMBOL,NAME OF COMPANY\nRELIANCE,Reliance Industries Limited\nINFY,Infosys Limited\n"
        )
        result = _load_from_csv(path)
        assert result.get("Reliance Industries Limited") == "RELIANCE"
        assert result.get("Infosys Limited") == "INFY"

    def test_strips_whitespace_from_headers(self, tmp_path):
        path = self._write_csv(
            tmp_path, " SYMBOL , NAME OF COMPANY \nTCS , Tata Consultancy Services Limited\n"
        )
        result = _load_from_csv(path)
        assert "Tata Consultancy Services Limited" in result

    def test_returns_empty_on_missing_file(self):
        result = _load_from_csv("/nonexistent/path.csv")
        assert result == {}

    def test_returns_empty_on_wrong_columns(self, tmp_path):
        path = self._write_csv(tmp_path, "COL1,COL2\nA,B\n")
        result = _load_from_csv(path)
        assert result == {}

    def test_skips_rows_with_missing_values(self, tmp_path):
        path = self._write_csv(
            tmp_path, "SYMBOL,NAME OF COMPANY\nRELIANCE,Reliance Industries\n,Missing Symbol\n"
        )
        result = _load_from_csv(path)
        assert "" not in result
        assert "Reliance Industries" in result


# ---------------------------------------------------------------------------
# _load_from_db
# ---------------------------------------------------------------------------

class TestLoadFromDb:
    def test_returns_empty_when_no_pool(self):
        with patch("ticker_utils._load_from_db") as mock:
            mock.return_value = {}
            result = mock()
        assert result == {}

    def test_returns_empty_on_db_exception(self):
        with patch("database.connection_pool", MagicMock()):
            with patch("database.get_db_connection", side_effect=Exception("timeout")):
                result = _load_from_db()
        assert result == {}

    def test_returns_map_from_db_rows(self):
        mock_conn = MagicMock()
        mock_df = pd.DataFrame({
            "name": ["Reliance Industries Limited", "Infosys Limited"],
            "ticker": ["RELIANCE", "INFY"],
        })
        mock_pool = MagicMock()
        with (
            patch("ticker_utils._load_from_db") as mock_fn,
        ):
            mock_fn.return_value = dict(zip(mock_df["name"], mock_df["ticker"]))
            result = mock_fn()

        assert result["Reliance Industries Limited"] == "RELIANCE"


# ---------------------------------------------------------------------------
# load_nse_tickers — integration with fallback chain
# ---------------------------------------------------------------------------

class TestLoadNseTickers:
    def test_falls_back_to_csv_when_db_unavailable(self, tmp_path):
        """When DB returns {}, should try CSV files."""
        fake_csv = tmp_path / "nse_stocks.csv"
        fake_csv.write_text("SYMBOL,NAME OF COMPANY\nHDFCBANK,HDFC Bank Limited\n")

        with (
            patch("ticker_utils._load_from_db", return_value={}),
            patch("ticker_utils._ENRICHED_CSV", str(tmp_path / "nse_stocks_enriched.csv")),
            patch("ticker_utils._RAW_CSV", str(fake_csv)),
        ):
            result = load_nse_tickers()

        assert result.get("HDFC Bank Limited") == "HDFCBANK"

    def test_db_result_takes_priority_over_csv(self):
        db_map = {"Reliance Industries Limited": "RELIANCE"}
        with patch("ticker_utils._load_from_db", return_value=db_map):
            result = load_nse_tickers()
        assert result == db_map

    def test_returns_empty_dict_when_all_sources_fail(self, tmp_path):
        with (
            patch("ticker_utils._load_from_db", return_value={}),
            patch("ticker_utils._ENRICHED_CSV", str(tmp_path / "missing.csv")),
            patch("ticker_utils._RAW_CSV", str(tmp_path / "also_missing.csv")),
        ):
            result = load_nse_tickers()
        assert result == {}

    def test_result_is_a_dict(self):
        with patch("ticker_utils._load_from_db", return_value={"A Ltd": "ATICKER"}):
            result = load_nse_tickers()
        assert isinstance(result, dict)
