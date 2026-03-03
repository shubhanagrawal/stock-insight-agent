# tests/test_inference_engine.py
"""Unit tests for inference_engine.py — generate_insight is a pure formatter."""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Patch core_nlp before importing inference_engine to avoid Groq client init
import unittest.mock
with unittest.mock.patch.dict("sys.modules", {
    "core_nlp": unittest.mock.MagicMock(),
    "groq": unittest.mock.MagicMock(),
}):
    from inference_engine import generate_insight


class TestGenerateInsight:
    def test_returns_string(self, sample_linked_tickers, sentiment_positive):
        result = generate_insight("HDFC Bank profit jumps", sample_linked_tickers, sentiment_positive)
        assert isinstance(result, str)

    def test_contains_headline(self, sample_linked_tickers, sentiment_positive):
        title = "Reliance posts record profits"
        result = generate_insight(title, sample_linked_tickers, sentiment_positive)
        assert title in result

    def test_contains_ticker(self, sample_linked_tickers, sentiment_positive):
        result = generate_insight("headline", sample_linked_tickers, sentiment_positive)
        assert "RELIANCE" in result

    def test_positive_sentiment_shows_green_emoji(self, sample_linked_tickers, sentiment_positive):
        result = generate_insight("headline", sample_linked_tickers, sentiment_positive)
        assert "🟢" in result

    def test_negative_sentiment_shows_red_emoji(self, sample_linked_tickers, sentiment_negative):
        result = generate_insight("headline", sample_linked_tickers, sentiment_negative)
        assert "🔴" in result

    def test_neutral_sentiment_shows_yellow_emoji(self, sample_linked_tickers, sentiment_neutral):
        result = generate_insight("headline", sample_linked_tickers, sentiment_neutral)
        assert "🟡" in result

    def test_confidence_percentage_shown(self, sample_linked_tickers, sentiment_positive):
        result = generate_insight("headline", sample_linked_tickers, sentiment_positive)
        assert "90%" in result

    def test_empty_tickers_shows_na(self, sentiment_positive):
        result = generate_insight("Some headline", {}, sentiment_positive)
        assert "N/A" in result

    def test_multiple_tickers_joined(self, sentiment_positive):
        tickers = {
            "Reliance Industries Limited": {"ticker": "RELIANCE", "ner_name": "Reliance", "score": 95},
            "Infosys Limited": {"ticker": "INFY", "ner_name": "Infosys", "score": 92},
        }
        result = generate_insight("headline", tickers, sentiment_positive)
        assert "RELIANCE" in result
        assert "INFY" in result
