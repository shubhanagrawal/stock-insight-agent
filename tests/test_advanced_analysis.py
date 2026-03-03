# tests/test_advanced_analysis.py
"""Unit tests for advanced_analysis.py — no external API calls needed (TextBlob + keywords)."""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from advanced_analysis import (
    AdvancedSentimentAnalyzer,
    TradingSignalGenerator,
    NewsImpactCalculator,
)


# ---------------------------------------------------------------------------
# AdvancedSentimentAnalyzer
# ---------------------------------------------------------------------------

class TestAdvancedSentimentAnalyzer:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.analyzer = AdvancedSentimentAnalyzer()

    def test_returns_dict(self):
        result = self.analyzer.analyze_advanced_sentiment("Profit surged 30%")
        assert isinstance(result, dict)

    def test_result_has_required_keys(self):
        result = self.analyzer.analyze_advanced_sentiment("Revenue grew strongly")
        assert "sentiment" in result
        assert "confidence" in result
        assert "score" in result

    def test_positive_keywords_give_positive_sentiment(self):
        result = self.analyzer.analyze_advanced_sentiment(
            "Profit growth record expansion revenue surge"
        )
        assert result["sentiment"] == "Positive"

    def test_negative_keywords_give_negative_sentiment(self):
        result = self.analyzer.analyze_advanced_sentiment(
            "Loss bankruptcy decline fraud default debt crisis"
        )
        assert result["sentiment"] == "Negative"

    def test_empty_string_returns_neutral(self):
        result = self.analyzer.analyze_advanced_sentiment("")
        assert result["sentiment"] == "Neutral"

    def test_confidence_between_zero_and_one(self):
        result = self.analyzer.analyze_advanced_sentiment("Mixed market signals today")
        assert 0.0 <= result["confidence"] <= 1.0


# ---------------------------------------------------------------------------
# TradingSignalGenerator
# ---------------------------------------------------------------------------

class TestTradingSignalGenerator:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.generator = TradingSignalGenerator()

    def _make_stock_data(self, change_pct=1.0):
        """Minimal stock data dict accepted by the generator."""
        import pandas as pd
        dates = pd.date_range(end=pd.Timestamp.today(), periods=30, freq="B")
        close = [100 + i * change_pct for i in range(30)]
        return pd.DataFrame({"Close": close, "Volume": [1_000_000] * 30}, index=dates)

    def test_returns_dict(self, sentiment_positive):
        stock_df = self._make_stock_data(change_pct=0.5)
        result = self.generator.generate_trading_signal(sentiment_positive, stock_df)
        assert isinstance(result, dict)

    def test_result_has_recommendation_key(self, sentiment_positive):
        stock_df = self._make_stock_data()
        result = self.generator.generate_trading_signal(sentiment_positive, stock_df)
        assert "recommendation" in result

    def test_result_has_confidence_key(self, sentiment_positive):
        stock_df = self._make_stock_data()
        result = self.generator.generate_trading_signal(sentiment_positive, stock_df)
        assert "confidence" in result

    def test_positive_sentiment_uptrend_gives_buy_signal(self, sentiment_positive):
        stock_df = self._make_stock_data(change_pct=2.0)  # strong uptrend
        result = self.generator.generate_trading_signal(sentiment_positive, stock_df)
        assert result["recommendation"] in ("Strong Buy", "Buy", "Hold")

    def test_negative_sentiment_downtrend_gives_sell_signal(self, sentiment_negative):
        stock_df = self._make_stock_data(change_pct=-2.0)  # strong downtrend
        result = self.generator.generate_trading_signal(sentiment_negative, stock_df)
        assert result["recommendation"] in ("Strong Sell", "Sell", "Hold")


# ---------------------------------------------------------------------------
# NewsImpactCalculator
# ---------------------------------------------------------------------------

class TestNewsImpactCalculator:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.calc = NewsImpactCalculator()

    def test_returns_dict_with_score(self, sentiment_positive):
        result = self.calc.calculate_impact_score(
            "Reliance Q4 earnings beat estimates",
            "Profit rose 25% in Q4 results",
            sentiment_positive,
        )
        assert "score" in result

    def test_earnings_keyword_raises_score(self, sentiment_positive):
        result_earnings = self.calc.calculate_impact_score(
            "Earnings results Q4 quarterly",
            "Record quarterly earnings",
            sentiment_positive,
        )
        result_plain = self.calc.calculate_impact_score(
            "General market update",
            "Markets were flat today",
            sentiment_positive,
        )
        assert result_earnings["score"] >= result_plain["score"]

    def test_score_is_non_negative(self, sentiment_negative):
        result = self.calc.calculate_impact_score("Title", "Content", sentiment_negative)
        assert result["score"] >= 0
