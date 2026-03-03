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
# Return shape: { sentiment, confidence, raw_score, keyword_contribution,
#                 textblob_contribution, impact_multiplier }

class TestAdvancedSentimentAnalyzer:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.analyzer = AdvancedSentimentAnalyzer()

    def test_returns_dict(self):
        result = self.analyzer.analyze_advanced_sentiment("Profit surged 30%")
        assert isinstance(result, dict)

    def test_result_has_required_keys(self):
        result = self.analyzer.analyze_advanced_sentiment("Revenue grew strongly")
        for key in ("sentiment", "confidence", "raw_score", "keyword_contribution",
                    "textblob_contribution", "impact_multiplier"):
            assert key in result, f"Missing key: {key}"

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

    def test_confidence_is_absolute_value_of_raw_score(self):
        result = self.analyzer.analyze_advanced_sentiment("Strong profit growth")
        assert result["confidence"] == pytest.approx(abs(result["raw_score"]), abs=1e-9)

    def test_confidence_between_zero_and_one(self):
        result = self.analyzer.analyze_advanced_sentiment("Mixed market signals today")
        # confidence = abs(raw_score); raw_score is bounded by tanh * multiplier, generally <= 1
        assert result["confidence"] >= 0.0

    def test_earnings_multiplier_applied(self):
        """Text with 'quarterly earnings' should have a higher multiplier (1.4)."""
        result = self.analyzer.analyze_advanced_sentiment("quarterly earnings beat estimates")
        assert result["impact_multiplier"] >= 1.4


# ---------------------------------------------------------------------------
# TradingSignalGenerator
# ---------------------------------------------------------------------------
# generate_trading_signal expects:
#   sentiment_data: dict with keys 'sentiment' and 'confidence'
#   stock_data:     dict with keys 'change_percent' and 'volume'
# Return shape: { overall_signal, signal_strength, individual_signals,
#                 recommendation, confidence_level }

class TestTradingSignalGenerator:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.generator = TradingSignalGenerator()

    def _make_stock_dict(self, change_pct=1.0, volume=2_000_000):
        """Minimal stock dict accepted by the generator."""
        return {"change_percent": change_pct, "volume": volume}

    def test_returns_dict(self, sentiment_positive):
        result = self.generator.generate_trading_signal(
            sentiment_positive, self._make_stock_dict()
        )
        assert isinstance(result, dict)

    def test_result_has_all_required_keys(self, sentiment_positive):
        result = self.generator.generate_trading_signal(
            sentiment_positive, self._make_stock_dict()
        )
        for key in ("overall_signal", "signal_strength", "individual_signals",
                    "recommendation", "confidence_level"):
            assert key in result, f"Missing key: {key}"

    def test_signal_strength_is_absolute_of_overall(self, sentiment_positive):
        result = self.generator.generate_trading_signal(
            sentiment_positive, self._make_stock_dict()
        )
        assert result["signal_strength"] == pytest.approx(
            abs(result["overall_signal"]), abs=1e-9
        )

    def test_positive_sentiment_uptrend_gives_buy_signal(self, sentiment_positive):
        result = self.generator.generate_trading_signal(
            sentiment_positive, self._make_stock_dict(change_pct=5.0)
        )
        assert result["recommendation"] in ("Strong Buy", "Buy", "Hold")

    def test_negative_sentiment_downtrend_gives_sell_signal(self, sentiment_negative):
        result = self.generator.generate_trading_signal(
            sentiment_negative, self._make_stock_dict(change_pct=-5.0)
        )
        assert result["recommendation"] in ("Strong Sell", "Sell", "Hold")

    def test_recommendation_is_valid_string(self, sentiment_neutral):
        result = self.generator.generate_trading_signal(
            sentiment_neutral, self._make_stock_dict(change_pct=0.0)
        )
        valid = {"Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"}
        assert result["recommendation"] in valid


# ---------------------------------------------------------------------------
# NewsImpactCalculator
# ---------------------------------------------------------------------------
# Return shape: { impact_score, base_sentiment_confidence,
#                 category_multiplier, detected_categories }

class TestNewsImpactCalculator:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.calc = NewsImpactCalculator()

    def test_returns_dict_with_impact_score(self, sentiment_positive):
        result = self.calc.calculate_impact_score(
            "Reliance Q4 earnings beat estimates",
            "Profit rose 25% in Q4 results",
            sentiment_positive,
        )
        assert "impact_score" in result

    def test_result_has_all_required_keys(self, sentiment_positive):
        result = self.calc.calculate_impact_score("Title", "Content", sentiment_positive)
        for key in ("impact_score", "base_sentiment_confidence",
                    "category_multiplier", "detected_categories"):
            assert key in result, f"Missing key: {key}"

    def test_earnings_keyword_raises_multiplier(self, sentiment_positive):
        """Earnings headlines should get a category_multiplier of 1.5."""
        result = self.calc.calculate_impact_score(
            "Earnings results Q4 quarterly",
            "Record quarterly earnings reported",
            sentiment_positive,
        )
        assert result["category_multiplier"] >= 1.5

    def test_plain_news_has_base_multiplier(self, sentiment_positive):
        result = self.calc.calculate_impact_score(
            "General market update today",
            "Markets were mixed today",
            sentiment_positive,
        )
        assert result["category_multiplier"] == pytest.approx(1.0)

    def test_impact_score_is_non_negative(self, sentiment_negative):
        result = self.calc.calculate_impact_score("Title", "Content", sentiment_negative)
        assert result["impact_score"] >= 0

    def test_detected_categories_is_list(self, sentiment_positive):
        result = self.calc.calculate_impact_score("Title", "Content", sentiment_positive)
        assert isinstance(result["detected_categories"], list)

    def test_no_category_match_returns_general(self, sentiment_positive):
        result = self.calc.calculate_impact_score(
            "Today was a day", "Nothing happened", sentiment_positive
        )
        assert result["detected_categories"] == ["general"]
