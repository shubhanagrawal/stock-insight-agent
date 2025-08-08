# SEGMENT 3: scraper.py (FIXED)
import feedparser
import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)

RSS_FEED_URL = "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"

def get_article_content(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            article = soup.find('div', class_='Normal') or soup.find('article')
            return article.get_text(strip=True) if article else None
        return None
    except Exception as e:
        logging.warning(f"Error fetching article content from {url}: {e}")
        return None

def scrape_news(limit=1):
    logging.info("Attempting to fetch RSS feed...")
    feed = feedparser.parse(RSS_FEED_URL)
    articles = []

    if 'entries' not in feed or not feed.entries:
        logging.warning("No articles found in RSS feed.")
        return articles

    logging.info("RSS feed fetch successful. Parsing feed...")
    for entry in feed.entries[:limit]:
        title = entry.title
        link = entry.link
        logging.info(f"Found article: {title}")
        content = get_article_content(link)
        if content:
            articles.append({"title": title, "link": link, "content": content})
            logging.info(f"Successfully scraped article: \"{title}\"")
        else:
            logging.warning(f"Could not scrape full content for article: \"{title}\"")

    return articles
