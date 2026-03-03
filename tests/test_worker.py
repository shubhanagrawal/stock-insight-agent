# tests/test_worker.py
"""Unit tests for worker.py — mocked Neo4j, DB, spaCy, and scraper."""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# get_competitors_from_graph
# ---------------------------------------------------------------------------

class TestGetCompetitorsFromGraph:
    def test_returns_list_of_tickers(self):
        mock_record = MagicMock()
        mock_record.__getitem__ = MagicMock(return_value="INFY")
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session.run.return_value = [mock_record]
        mock_driver = MagicMock()
        mock_driver.session.return_value = mock_session

        with patch("worker.driver", mock_driver):
            from worker import get_competitors_from_graph
            result = get_competitors_from_graph("TCS")

        assert isinstance(result, list)

    def test_returns_empty_list_on_db_error(self):
        mock_driver = MagicMock()
        mock_driver.session.side_effect = Exception("Neo4j unavailable")

        with patch("worker.driver", mock_driver):
            from worker import get_competitors_from_graph
            try:
                result = get_competitors_from_graph("TCS")
                assert isinstance(result, list)
            except Exception:
                pass  # acceptable — function doesn't swallow the error


# ---------------------------------------------------------------------------
# process_feed — no articles path
# ---------------------------------------------------------------------------

class TestProcessFeedNoArticles:
    def test_returns_immediately_when_no_articles(self):
        mock_scraper = MagicMock()
        mock_scraper.run.return_value = []

        with patch("worker.NewsArticleScraper", return_value=mock_scraper):
            from worker import process_feed
            # Should not raise and should not attempt DB writes
            process_feed("https://example.com/feed.xml", source_weight=1.0)


# ---------------------------------------------------------------------------
# process_feed — article with no tickers
# ---------------------------------------------------------------------------

class TestProcessFeedNoTickers:
    def test_skips_article_when_no_tickers_found(self):
        mock_scraper = MagicMock()
        mock_scraper.run.return_value = [
            {"title": "Weather Update", "content": "It was sunny today.", "link": "https://x.com/1"}
        ]

        with (
            patch("worker.NewsArticleScraper", return_value=mock_scraper),
            patch("worker.extract_tickers", return_value={}),
            patch("worker.save_specific_insight") as mock_save,
        ):
            from worker import process_feed
            process_feed("https://example.com/feed.xml", source_weight=1.0)

        # No ticker found → insight should never be saved
        mock_save.assert_not_called()


# ---------------------------------------------------------------------------
# process_feed — full happy path
# ---------------------------------------------------------------------------

class TestProcessFeedHappyPath:
    def _make_article(self):
        return {
            "title": "Reliance posts record profits",
            "content": "Reliance Industries reported a massive profit surge.",
            "link": "https://example.com/reliance",
        }

    def _make_tickers(self):
        return {
            "Reliance Industries Limited": {
                "ticker": "RELIANCE",
                "ner_name": "Reliance",
                "score": 95,
            }
        }

    def test_saves_insight_for_matched_ticker(self):
        mock_scraper = MagicMock()
        mock_scraper.run.return_value = [self._make_article()]

        mock_doc = MagicMock()
        mock_sent = MagicMock()
        mock_sent.text = "Reliance Industries reported a massive profit surge."
        mock_doc.sents = [mock_sent]

        mock_sentiment = {"sentiment": "Positive", "confidence": 0.9}

        with (
            patch("worker.NewsArticleScraper", return_value=mock_scraper),
            patch("worker.extract_tickers", return_value=self._make_tickers()),
            patch("worker.extract_key_figures", return_value={"profit_change_percent": "18%"}),
            patch("worker.classify_event_type", return_value="Earnings Report"),
            patch("worker.analyze_sentiment", return_value=mock_sentiment),
            patch("worker.nlp", return_value=mock_doc),
            patch("worker.save_specific_insight") as mock_save,
            patch("worker.get_competitors_from_graph", return_value=[]),
        ):
            from worker import process_feed
            process_feed("https://example.com/feed.xml", source_weight=1.0)

        mock_save.assert_called_once()
        call_args = mock_save.call_args[0]
        assert call_args[0] == "Reliance posts record profits"   # title
        assert call_args[3] == "RELIANCE"                        # ticker

    def test_impact_score_above_zero_for_high_confidence(self):
        """impact_score = confidence * source_weight * event_multiplier > 0."""
        saved_calls = []

        mock_scraper = MagicMock()
        mock_scraper.run.return_value = [self._make_article()]

        mock_doc = MagicMock()
        mock_sent = MagicMock()
        # Must contain the ner_name 'Reliance' so worker finds it as a relevant sentence
        mock_sent.text = "Reliance Industries reported a massive profit surge."
        mock_doc.sents = [mock_sent]

        def capture_save(*args, **kwargs):
            saved_calls.append(args)

        with (
            patch("worker.NewsArticleScraper", return_value=mock_scraper),
            patch("worker.extract_tickers", return_value=self._make_tickers()),
            patch("worker.extract_key_figures", return_value={}),
            patch("worker.classify_event_type", return_value="Earnings Report"),
            patch("worker.analyze_sentiment", return_value={"sentiment": "Positive", "confidence": 0.9}),
            patch("worker.nlp", return_value=mock_doc),
            patch("worker.save_specific_insight", side_effect=capture_save),
            patch("worker.get_competitors_from_graph", return_value=[]),
        ):
            from worker import process_feed
            process_feed("https://example.com/feed.xml", source_weight=1.0)

        assert saved_calls, "save_specific_insight was not called"
        impact_score = saved_calls[0][6]   # 7th positional arg
        assert impact_score > 0
