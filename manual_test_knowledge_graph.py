# test_knowledge_graph.py
import logging
import spacy
import json

# Import the specific functions we need to test
from nlp_processor import extract_tickers
from core_nlp import analyze_sentiment_core as analyze_sentiment # Use the core, non-cached version for testing
from worker import get_competitors_from_graph, COMPETITIVE_KEYWORDS

# --- Setup ---
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s: %(message)s')
nlp = spacy.load("en_core_web_lg")

def test_competitive_logic(article: dict):
    """
    Simulates the worker's logic for a single article to test the knowledge graph.
    """
    title = article.get("title", "")
    content = article.get("content", "")
    
    # Extract all tickers found in the article
    primary_tickers = extract_tickers(title) or extract_tickers(content)
    if not primary_tickers:
        logging.warning("Test failed: No tickers were extracted from the sample article.")
        return

    # --- This is the core logic from your worker ---
    sentiment_results = {}
    doc = nlp(content)
    for company_name, data in primary_tickers.items():
        ner_name = data['ner_name']
        relevant_sentences = [sent.text for sent in doc.sents if ner_name in sent.text]
        if relevant_sentences:
            sentiment_results[data['ticker']] = analyze_sentiment(" ".join(relevant_sentences))

    # Rule Engine: Check for competitive context
    tickers_in_headline = {data['ticker'] for data in (extract_tickers(title) or {}).values()}
    if len(tickers_in_headline) > 1 and any(kw in title.lower() for kw in COMPETITIVE_KEYWORDS):
        logging.info("Competitive context detected. Applying relationship rules.")
        
        winner = next((ticker for ticker, result in sentiment_results.items() if result.get('sentiment') == 'Positive'), None)
        
        if winner:
            logging.info(f"Identified Winner: {winner}")
            # Query the knowledge graph for competitors
            competitors = get_competitors_from_graph(winner)
            logging.info(f"Found competitors for {winner} in graph: {competitors}")
            
            loser = next((comp for comp in competitors if comp in tickers_in_headline), None)
            
            if loser:
                # Apply the rule: override the loser's sentiment
                logging.info(f"GRAPH RULE APPLIED: {winner} (Winner) -> {loser} (Loser). Setting sentiment for {loser} to Negative.")
                sentiment_results[loser] = {'sentiment': 'Negative', 'confidence': 0.98}
                print("\n--- TEST SUCCESSFUL ---")
                print(f"Final Sentiment for {winner}: {sentiment_results[winner]['sentiment']}")
                print(f"Final Sentiment for {loser}: {sentiment_results[loser]['sentiment']}")
                return
    
    print("\n--- TEST FAILED ---")
    print("The competitive relationship logic was not triggered or failed.")
    print("Final sentiments:", sentiment_results)


if __name__ == "__main__":
    # A perfect sample headline to trigger the logic
    sample_article = {
        "title": "Infosys wins multi-billion dollar AI deal, beats out rival Wipro",
        "content": "In a major win for the Indian IT sector, Infosys announced today it has secured a landmark artificial intelligence contract. The deal, valued at over $2 billion, positions Infosys as a leader in the space. The contract was highly contested, with sources confirming that Infosys beats out rival Wipro in the final bidding stages. This is a significant setback for Wipro."
    }
    
    test_competitive_logic(sample_article)