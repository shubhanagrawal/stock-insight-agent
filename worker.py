# worker.py
import logging
import json
import spacy
from scraper import NewsArticleScraper
from nlp_processor import extract_tickers, extract_key_figures
from core_nlp import analyze_sentiment_core as analyze_sentiment
from core_nlp import classify_event_type_core as classify_event_type
from database import save_specific_insight
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
from config import COMPETITIVE_KEYWORDS, EVENT_IMPACT_MULTIPLIERS

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s: %(message)s')
nlp = spacy.load("en_core_web_lg")
load_dotenv()

# Knowledge Graph Connection
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

def get_competitors_from_graph(ticker: str) -> list:
    with driver.session() as session:
        query = "MATCH (:Company {ticker: $ticker})-[:IN_SECTOR]->()<-[:IN_SECTOR]-(c:Company) RETURN c.ticker AS competitor"
        result = session.run(query, ticker=ticker)
        return [record["competitor"] for record in result]

def process_feed(feed_url: str, source_weight: float, article_limit: int = 5):
    try:
        scraper = NewsArticleScraper()
        articles = scraper.run(feed_url=feed_url, limit=article_limit)
        if not articles: return

        for article in articles:
            title, content, link = article.get("title", ""), article.get("content", ""), article.get("link", "#")

            primary_tickers = extract_tickers(title) or extract_tickers(content)
            if not primary_tickers: continue

            key_figures = extract_key_figures(content)
            event_type = classify_event_type(title)
            event_multiplier = EVENT_IMPACT_MULTIPLIERS.get(event_type, 1.0)
            
            doc = nlp(content)
            sentiment_results = {}
            for company_name, data in primary_tickers.items():
                ner_name = data['ner_name']
                relevant_sentences = [sent.text for sent in doc.sents if ner_name in sent.text]
                if relevant_sentences:
                    sentiment_results[data['ticker']] = analyze_sentiment(" ".join(relevant_sentences))

            tickers_in_headline = {data['ticker'] for data in (extract_tickers(title) or {}).values()}
            if len(tickers_in_headline) > 1 and any(kw in title.lower() for kw in COMPETITIVE_KEYWORDS):
                winner = next((ticker for ticker, res in sentiment_results.items() if res.get('sentiment') == 'Positive'), None)
                if winner:
                    competitors = get_competitors_from_graph(winner)
                    loser = next((comp for comp in competitors if comp in tickers_in_headline), None)
                    if loser:
                        logging.info(f"GRAPH RULE APPLIED: {winner} -> {loser}. Setting sentiment for {loser} to Negative.")
                        sentiment_results[loser] = {'sentiment': 'Negative', 'confidence': 0.98}

            for company_name, data in primary_tickers.items():
                ticker = data['ticker']
                if ticker in sentiment_results:
                    sentiment_result = sentiment_results[ticker]
                    impact_score = sentiment_result.get('confidence', 0.0) * source_weight * event_multiplier
                    save_specific_insight(
                        title, link, company_name, ticker, sentiment_result, 
                        event_type, impact_score, json.dumps(key_figures)
                    )
    except Exception as e:
        logging.error(f"Error in worker pipeline: {e}", exc_info=True)