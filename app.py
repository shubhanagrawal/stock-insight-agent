# Import the functions from our other files
from scraper import fetch_latest_article
from nlp_processor import get_tickers_from_text # UPDATED import

def main():
    """
    This is the main function that runs our AI agent's pipeline.
    """
    print("🚀 Starting the AI Insight Agent...")
    
    # --- STAGE 1: SCRAPING ---
    print("\n--- STAGE 1: SCRAPING ---")
    article_data = fetch_latest_article()
    
    if not article_data:
        print("Could not fetch article. Exiting.")
        return

    print(f"Successfully scraped article: {article_data['title']}")
    
    # --- STAGE 2: NLP PROCESSING with Gemini ---
    # This is now a single, powerful step.
    print("\n--- STAGE 2: NLP PROCESSING ---")
    linked_tickers = get_tickers_from_text(article_data['text'])
    
    if not linked_tickers:
        print("No known company tickers found in the article.")
        return
        
    print(f"LLM found the following tickers: {linked_tickers}")
    print("\n✅ Pipeline complete.")


if __name__ == "__main__":
    main()