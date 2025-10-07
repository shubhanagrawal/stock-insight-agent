# SEGMENT 3: scraper.py (FIXED)
import feedparser
import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s: %(message)s')

def get_article_content(url):
    """
    Fetches and parses the full content of a news article from its URL.
    """
    try:
        # Use a user-agent to mimic a real browser
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raises an exception for bad status codes (4xx or 5xx)

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the main article content (selectors might need adjustment for different sites)
        article_body = soup.find('div', class_='Normal') or soup.find('article')
        
        if article_body:
            return article_body.get_text(separator=' ', strip=True)
        else:
            logging.warning(f"Could not find a valid article body at {url}")
            return None
            
    except requests.RequestException as e:
        logging.warning(f"Error fetching article content from {url}: {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred in get_article_content for {url}: {e}")
        return None

def scrape_news(url, limit=3):
    """
    Scrapes a given number of articles from a specified RSS feed URL.
    """
    logging.info(f"Attempting to fetch RSS feed from: {url}")
    feed = feedparser.parse(url)
    articles = []

    if feed.bozo:
        logging.warning(f"Error parsing RSS feed. It may be malformed. Bozo Exception: {feed.bozo_exception}")
        return articles
        
    if not feed.entries:
        logging.warning("No articles found in RSS feed.")
        return articles

    logging.info("RSS feed fetch successful. Parsing entries...")
    for entry in feed.entries[:limit]:
        title = entry.get('title', 'No Title')
        link = entry.get('link')
        
        if not link:
            logging.warning(f"Skipping article with no link: \"{title}\"")
            continue
            
        logging.info(f"Scraping content for: \"{title}\"")
        content = get_article_content(link)
        
        if content:
            articles.append({"title": title, "link": link, "content": content})
            logging.info(f"Successfully scraped: \"{title}\"")
        else:
            # Fallback to summary if full content fails
            summary = entry.get('summary', 'No content available.')
            articles.append({"title": title, "link": link, "content": summary})
            logging.warning(f"Using summary for: \"{title}\" as full content could not be scraped.")
            
    return articles