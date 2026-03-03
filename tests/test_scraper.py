# tests/test_scraper.py
"""Unit tests for scraper.py — pure methods and mocked HTTP / feedparser calls."""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scraper import NewsArticleScraper, scrape_news


# ---------------------------------------------------------------------------
# Pure / static methods
# ---------------------------------------------------------------------------

class TestCleanText:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.scraper = NewsArticleScraper()

    def test_collapses_multiple_whitespace(self):
        result = self.scraper._clean_text("Hello    world")
        assert result == "Hello world"

    def test_strips_leading_trailing_whitespace(self):
        result = self.scraper._clean_text("   hello   ")
        assert result == "hello"

    def test_preserves_single_spaces(self):
        result = self.scraper._clean_text("one two three")
        assert result == "one two three"

    def test_empty_string(self):
        assert self.scraper._clean_text("") == ""

    def test_newlines_collapsed_to_space(self):
        result = self.scraper._clean_text("line1\nline2\n\nline3")
        assert "\n" not in result


class TestRemoveUnwantedElements:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.scraper = NewsArticleScraper()

    def test_removes_script_tags(self):
        soup = BeautifulSoup("<div><script>alert(1)</script><p>Content</p></div>", "html.parser")
        self.scraper._remove_unwanted_elements(soup)
        assert soup.find("script") is None

    def test_removes_nav_tags(self):
        soup = BeautifulSoup("<nav>Menu</nav><p>Article</p>", "html.parser")
        self.scraper._remove_unwanted_elements(soup)
        assert soup.find("nav") is None

    def test_preserves_article_content(self):
        soup = BeautifulSoup("<p>Important article text</p>", "html.parser")
        self.scraper._remove_unwanted_elements(soup)
        assert "Important article text" in soup.get_text()


# ---------------------------------------------------------------------------
# _get_article_content — mocked HTTP
# ---------------------------------------------------------------------------

class TestGetArticleContent:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.scraper = NewsArticleScraper()
        # Replace session so no real HTTP happens
        self.scraper.session = MagicMock()

    def _make_response(self, html: str, status: int = 200):
        mock_resp = MagicMock()
        mock_resp.text = html
        mock_resp.raise_for_status = MagicMock()
        mock_resp.status_code = status
        return mock_resp

    def test_skips_video_urls(self):
        result = self.scraper._get_article_content("https://example.com/videoshow/123.cms")
        assert result is None

    def test_returns_text_from_matching_selector(self):
        html = "<div class='artText'>{}</div>".format("A" * 200)
        self.scraper.session.get.return_value = self._make_response(html)
        result = self.scraper._get_article_content("https://example.com/article")
        assert result is not None
        assert len(result) >= 150

    def test_returns_none_for_short_content(self):
        html = "<p>Too short</p>"
        self.scraper.session.get.return_value = self._make_response(html)
        result = self.scraper._get_article_content("https://example.com/short")
        assert result is None


# ---------------------------------------------------------------------------
# scrape_news convenience wrapper — mocked feedparser
# ---------------------------------------------------------------------------

class TestScrapeNews:
    def _make_feed(self, titles):
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [
            MagicMock(title=t, link=f"https://example.com/{i}", summary="<p>summary</p>")
            for i, t in enumerate(titles)
        ]
        return mock_feed

    def test_returns_list(self):
        with (
            patch("feedparser.parse", return_value=self._make_feed(["Article 1"])),
            patch.object(NewsArticleScraper, "_get_article_content", return_value="A" * 200),
        ):
            result = scrape_news("https://example.com/feed.xml", limit=1)
        assert isinstance(result, list)

    def test_respects_limit(self):
        with (
            patch("feedparser.parse", return_value=self._make_feed(["A", "B", "C", "D"])),
            patch.object(NewsArticleScraper, "_get_article_content", return_value="A" * 200),
        ):
            result = scrape_news("https://example.com/feed.xml", limit=2)
        assert len(result) <= 2

    def test_each_article_has_title_and_content(self):
        with (
            patch("feedparser.parse", return_value=self._make_feed(["Markets rally"])),
            patch.object(NewsArticleScraper, "_get_article_content", return_value="A" * 200),
        ):
            result = scrape_news("https://example.com/feed.xml", limit=1)
        if result:
            assert "title" in result[0]
            assert "content" in result[0]

    def test_malformed_feed_returns_empty_list(self):
        mock_feed = MagicMock()
        mock_feed.bozo = True
        mock_feed.entries = []
        with patch("feedparser.parse", return_value=mock_feed):
            result = scrape_news("https://bad-feed.example.com/")
        assert result == []
