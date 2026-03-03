# tests/test_nlp_processor.py
"""Unit tests for nlp_processor.py — ticker extraction and key figure extraction."""

import sys
import os
import re
import pytest
from unittest.mock import patch, MagicMock

# Make sure the project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# Helpers — pure functions from nlp_processor
# ---------------------------------------------------------------------------

from nlp_processor import _normalize_text, _build_normalized_index


class TestNormalizeText:
    def test_lowercases_input(self):
        assert _normalize_text("Reliance Industries") == "reliance industries"

    def test_replaces_punctuation_with_space(self):
        assert _normalize_text("L&T Finance") == "l t finance"

    def test_strips_leading_trailing_whitespace(self):
        assert _normalize_text("  HDFC  ") == "hdfc"

    def test_empty_string(self):
        assert _normalize_text("") == ""


class TestBuildNormalizedIndex:
    def test_official_name_is_indexed(self, sample_nse_map):
        index = _build_normalized_index(sample_nse_map)
        assert "reliance industries limited" in index

    def test_short_form_without_suffix_is_indexed(self, sample_nse_map):
        """'limited'/'ltd' suffixes should be stripped and also indexed."""
        index = _build_normalized_index(sample_nse_map)
        assert "reliance industries" in index

    def test_correct_ticker_returned(self, sample_nse_map):
        index = _build_normalized_index(sample_nse_map)
        official_name, ticker = index["reliance industries limited"]
        assert ticker == "RELIANCE"

    def test_empty_map_returns_empty_index(self):
        assert _build_normalized_index({}) == {}


# ---------------------------------------------------------------------------
# extract_tickers — uses mocked NSE map and spaCy
# ---------------------------------------------------------------------------

class TestExtractTickers:
    def _run_extraction(self, text, nse_map, ner_entities=None):
        """Helper: patches NSE_TICKER_MAP and spaCy inside nlp_processor."""
        import nlp_processor

        # Build a mock spaCy doc whose .ents returns given ORG entities
        mock_ent = MagicMock()
        mock_ent.label_ = "ORG"
        mock_ent.text = ner_entities[0] if ner_entities else ""
        mock_doc = MagicMock()
        mock_doc.ents = [mock_ent] if ner_entities else []

        mock_nlp = MagicMock(return_value=mock_doc)

        with (
            patch.object(nlp_processor, "NSE_TICKER_MAP", nse_map),
            patch.object(nlp_processor, "NORMALIZED_INDEX",
                         _build_normalized_index(nse_map)),
            patch.object(nlp_processor, "nlp", mock_nlp),
        ):
            return nlp_processor.extract_tickers(text)

    def test_exact_company_name_match(self, sample_nse_map):
        result = self._run_extraction(
            "Reliance Industries saw huge gains today.",
            sample_nse_map,
            ner_entities=["Reliance Industries"],
        )
        assert any(data["ticker"] == "RELIANCE" for data in result.values())

    def test_empty_text_returns_empty_dict(self, sample_nse_map):
        result = self._run_extraction("", sample_nse_map)
        assert result == {}

    def test_empty_nse_map_returns_empty_dict(self):
        from nlp_processor import extract_tickers
        with patch("nlp_processor.NSE_TICKER_MAP", {}):
            assert extract_tickers("Reliance posted profits.") == {}

    def test_blocklisted_entity_is_excluded(self, sample_nse_map):
        """SEBI is in the blocklist and should never appear as a ticker."""
        result = self._run_extraction(
            "SEBI announced new regulations today.",
            sample_nse_map,
            ner_entities=["SEBI"],
        )
        tickers = [d["ticker"] for d in result.values()]
        assert "SEBI" not in tickers

    def test_result_contains_required_keys(self, sample_nse_map):
        result = self._run_extraction(
            "Infosys beat earnings estimates.",
            sample_nse_map,
            ner_entities=["Infosys"],
        )
        for data in result.values():
            assert "ticker" in data
            assert "ner_name" in data


# ---------------------------------------------------------------------------
# extract_key_figures — mocked spaCy entities
# ---------------------------------------------------------------------------

class TestExtractKeyFigures:
    def _make_mock_doc(self, entities):
        """Build a minimal mock spaCy doc from a list of (label, text, context) tuples."""
        mock_ents = []
        for label, text, ctx_text in entities:
            ent = MagicMock()
            ent.label_ = label
            ent.text = text
            ent.start = 5
            ent.end = 6
            mock_ents.append(ent)

        mock_doc = MagicMock()
        mock_doc.ents = mock_ents
        # context window returns lowercase context text
        mock_doc.__getitem__ = lambda self, key: MagicMock(
            text=entities[0][2] if entities else ""
        )
        return mock_doc

    def test_returns_empty_when_nlp_unavailable(self):
        import nlp_processor
        with patch.object(nlp_processor, "nlp", None):
            assert nlp_processor.extract_key_figures("some text") == {}

    def test_returns_empty_for_empty_text(self):
        import nlp_processor
        with patch.object(nlp_processor, "nlp", MagicMock()):
            assert nlp_processor.extract_key_figures("") == {}
