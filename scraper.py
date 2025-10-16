import feedparser
import requests
from bs4 import BeautifulSoup
import logging
import time
from typing import Optional, List, Dict
from urllib.parse import urlparse
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')

class NewsArticleScraper:
    """
    A robust, industry-grade news scraper that fetches content from RSS feeds,
    handles anti-bot measures, and uses multiple strategies to extract clean article text.
    """
    def __init__(self, timeout: int = 20, retry_attempts: int = 2, delay: float = 1.5):
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.delay = delay
        self.min_content_length = 150
        
        try:
            import cloudscraper
            self.session = cloudscraper.create_scraper()
            logging.info("Cloudscraper enabled for enhanced anti-bot protection.")
        except ImportError:
            self.session = requests.Session()
            logging.info("Cloudscraper not found. Using standard requests. For better results: pip install cloudscraper")
            
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        
        self.content_selectors = [
            'div.artText', 'div.Normal', 'div#content_wrapper', 'article.article',
            'div[itemprop="articleBody"]', 'div.article-content', 'div.story-content'
        ]
        self.unwanted_elements = [
            'script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe', 
            {'class': re.compile('ad|comment|share|related|promo|widget|banner|footer|header', re.I)},
            {'id': re.compile('ad|comment|share|related|promo|widget|banner|footer|header', re.I)}
        ]

    def _clean_text(self, text: str) -> str:
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _remove_unwanted_elements(self, soup: BeautifulSoup):
        for unwanted in self.unwanted_elements:
            for element in soup.find_all(unwanted):
                element.decompose()

    def _get_article_content(self, url: str) -> Optional[str]:
        if 'videoshow' in url.lower():
            logging.warning(f"Skipping video article: {url}")
            return None
            
        for attempt in range(self.retry_attempts):
            try:
                if attempt > 0:
                    time.sleep(self.delay * attempt)
                
                logging.info(f"Fetching content from: {url} (Attempt {attempt + 1})")
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()

                # Use response.text to let 'requests' handle character encoding
                soup = BeautifulSoup(response.text, 'html.parser')
                self._remove_unwanted_elements(soup)
                
                article_body = None
                for selector in self.content_selectors:
                    article_body = soup.select_one(selector)
                    if article_body:
                        text = self._clean_text(article_body.get_text(separator=' '))
                        if len(text) >= self.min_content_length:
                            logging.info(f"✓ Successfully scraped {len(text)} chars using selector '{selector}'")
                            return text
                
                logging.warning(f"No specific selector worked for {url}. Falling back to paragraph extraction.")
                paragraphs = soup.find_all('p')
                text = ' '.join([p.get_text(strip=True) for p in paragraphs])
                cleaned_text = self._clean_text(text)
                
                if len(cleaned_text) >= self.min_content_length:
                    return cleaned_text
                
                logging.warning(f"Could not extract valid content from {url}")
                return None
            
            except requests.RequestException as e:
                logging.warning(f"Request error on attempt {attempt + 1} for {url}: {e}")
        
        logging.error(f"All retry attempts failed for {url}")
        return None

    # Renamed this method to `run` to avoid name conflicts
    def run(self, feed_url: str, limit: int = 3) -> List[Dict[str, str]]:
        try:
            logging.info(f"Attempting to fetch RSS feed from: {feed_url}")
            feed = feedparser.parse(feed_url)
        except Exception as e:
            logging.error(f"Failed to parse RSS feed: {e}"); return []
            
        if feed.bozo or not feed.entries:
            logging.warning("No articles found or feed is malformed."); return []

        logging.info(f"RSS successful. Found {len(feed.entries)} entries. Processing up to {limit}.")
        articles = []
        
        for entry in feed.entries[:limit]:
            title = entry.get('title', 'No Title')
            link = entry.get('link')
            
            if not link:
                logging.warning(f"Skipping article with no link: \"{title}\""); continue
            
            content = self._get_article_content(link)
            
            if not content:
                summary_html = entry.get('summary', '<p>No content available.</p>')
                summary_soup = BeautifulSoup(summary_html, 'html.parser')
                content = self._clean_text(summary_soup.get_text(separator=' ', strip=True))
                logging.warning(f"✗ Using RSS summary for: \"{title}\"")
            
            articles.append({"title": title, "link": link, "content": content})
            time.sleep(self.delay)
        
        return articles

# --- CONVENIENCE FUNCTION ---
# This is the only function your dashboard.py will see.
# It creates an instance of the powerful scraper class and runs it.
# This means YOU DO NOT NEED TO CHANGE YOUR DASHBOARD.PY FILE.
def scrape_news(url: str, limit: int = 3) -> list:
    scraper = NewsArticleScraper()
    return scraper.run(feed_url=url, limit=limit)

# Example usage for testing this file directly
if __name__ == "__main__":
    test_urls = [
        "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms",
        "https://www.moneycontrol.com/rss/MCtopnews.xml",
    ]
    for feed_url in test_urls:
        print(f"\n{'#'*70}\nTesting feed: {feed_url}\n{'#'*70}\n")
        articles_result = scrape_news(feed_url, limit=2)
        for article in articles_result:
            print(f"Title: {article['title']}")
            print(f"Content Preview: {article['content'][:150]}...\n")