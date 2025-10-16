# worker.py
import logging
import json
import spacy
from scraper import NewsArticleScraper
from nlp_processor import extract_tickers, extract_key_figures
from inference_engine import analyze_sentiment, classify_event_type
from database import save_specific_insight

# Setup
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s: %(message)s')
nlp = spacy.load("en_core_web_lg")

# In worker.py

def process_feed(feed_url: str, source_weight: float, article_limit: int = 5):
    """The complete data processing pipeline with a Cascading Relevance Filter."""
    try:
        logging.info(f"--- Starting worker for feed: {feed_url} ---")
        scraper = NewsArticleScraper()
        articles = scraper.run(feed_url=feed_url, limit=article_limit)
        if not articles: return

        event_multipliers = {"Merger or Acquisition": 1.5, "Earnings Report": 1.4, "Legal or Regulatory Issue": 1.3}

        for article in articles:
            title = article.get("title", "(no title)")
            content = article.get("content", "")
            link = article.get("link", "#")

            # --- NEW: CASCADING RELEVANCE LOGIC ---
            # 1. Prioritize the headline. It's the strongest signal.
            primary_tickers = extract_tickers(title)
            
            # 2. If the headline has no tickers, fall back to the full content.
            if not primary_tickers:
                logging.info("No tickers in headline, analyzing full content for subject.")
                all_content_tickers = extract_tickers(content)
                if not all_content_tickers:
                    logging.warning("No actionable tickers found in article content."); continue

                # Use relevance scoring as a fallback method
                scored_tickers = []
                for company_name, data in all_content_tickers.items():
                    ner_name = data.get('ner_name', company_name)
                    frequency_score = content.lower().count(ner_name.lower())
                    relevance_score = frequency_score
                    scored_tickers.append((company_name, data, relevance_score))

                if not scored_tickers: continue
                primary_subject = max(scored_tickers, key=lambda item: item[2])
                
                # Only proceed if a clear subject is found (mentioned more than once)
                if primary_subject[2] <= 1: 
                    logging.warning("No single company stood out as the main subject. Skipping."); continue
                
                # Reconstruct the primary_tickers dict with only the top subject
                company_name, data, _ = primary_subject
                primary_tickers = {company_name: data}
            # ----------------------------------------

            key_figures = extract_key_figures(content)
            event_type = classify_event_type(title)
            event_multiplier = event_multipliers.get(event_type, 1.0)
            
            doc = nlp(content)
            for company_name, data in primary_tickers.items():
                ticker, ner_name = data['ticker'], data['ner_name']
                
                relevant_sentences = [sent.text for sent in doc.sents if ner_name in sent.text]
                if not relevant_sentences: continue

                company_specific_text = " ".join(relevant_sentences)
                sentiment_result = analyze_sentiment(company_specific_text)
                
                impact_score = sentiment_result.get('confidence', 0.0) * source_weight * event_multiplier
                
                save_specific_insight(
                    title, link, company_name, ticker, sentiment_result, 
                    event_type, impact_score, json.dumps(key_figures)
                )
    except Exception as e:
        logging.error(f"An error occurred in the worker pipeline: {e}", exc_info=True)