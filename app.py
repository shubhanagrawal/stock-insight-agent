# app.py
import logging
from scraper import scrape_news
from nlp_processor import extract_tickers
from inference_engine import analyze_sentiment, generate_insight
from config import FEEDS_TO_PROCESS

# Set up logging to see the output from all modules
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s: %(message)s')

def main():
    """
    Main pipeline for the AI Stock Insight Agent.
    This version processes multiple articles from the feed.
    """
    logging.info("🚀 Starting the AI Insight Agent...")

    # --- STAGE 1: SCRAPING ---
    # Collect articles from all configured feeds.
    articles = []
    for source_name, feed_config in FEEDS_TO_PROCESS.items():
        logging.info(f"Fetching from {source_name}...")
        fetched = scrape_news(url=feed_config['url'], limit=3)
        articles.extend(fetched)

    if not articles:
        logging.warning("Could not fetch any articles. Exiting.")
        return

    # --- Process each article found ---
    for article in articles:
        print("\n" + "~"*60) # Separator for clarity
        logging.info(f"Processing article: \"{article['title']}\"")

        # --- STAGE 2: NLP PROCESSING (Ticker Extraction) ---
        # We pass the scraped article's content to our new NLP processor.
        linked_tickers = extract_tickers(article['content'])
        
        if not linked_tickers:
            logging.warning("No actionable tickers found in this article. Moving to next article.")
            continue
            
        logging.info(f"🎯 Tickers Extracted: {linked_tickers}")
        
        # --- STAGE 3: INFERENCE (Sentiment Analysis) ---
        sentiment = analyze_sentiment(article['title'])
        logging.info(f"Sentiment analysis complete: {sentiment}")
        
        # --- FINAL STAGE: GENERATE & DISPLAY INSIGHT ---
        final_insight = generate_insight(article['title'], linked_tickers, sentiment)
        
        print("\n" + "="*50)
        logging.info("📊 Final Insight:")
        print(final_insight)
        print("="*50)

    print("\n✅ Agent run complete.")

if __name__ == "__main__":
    main()
