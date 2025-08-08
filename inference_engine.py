# inference_engine.py
import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# The specific URL for the FinBERT model on Hugging Face's Inference API
API_URL = "https://api-inference.huggingface.co/models/ProsusAI/finbert"
API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")
HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}

def analyze_sentiment(text):
    """
    Analyzes the sentiment of a given text by calling the Hugging Face Inference API.
    """
    # Defensive Check: Do not call the API if the text is empty.
    if not text or not text.strip():
        print("Sentiment analysis skipped: Input text is empty.")
        return "Neutral"

    if not API_TOKEN:
        print("Hugging Face API token not found. Defaulting to Neutral.")
        return "Neutral"

    # The API expects a JSON payload with the "inputs" key.
    # We add the "wait_for_model" option to prevent timeout errors.
    payload = {
        "inputs": text,
        "options": {"wait_for_model": True}
    }
    
    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        
        results = response.json()[0]
        
        # Find the label with the highest score
        best_result = max(results, key=lambda x: x['score'])
        return best_result['label'].capitalize()
        
    except Exception as e:
        print(f"Error during sentiment analysis API call: {e}")
        return "Neutral" # Return a default value on failure

def generate_insight(article_title, linked_tickers, sentiment):
    """
    Combines all gathered information into a final insight.
    (This function remains unchanged)
    """
    if not linked_tickers:
        return "No insights generated as no tickers were found."

    primary_company_name = list(linked_tickers.keys())[0]
    primary_ticker = linked_tickers[primary_company_name]
    
    if sentiment == "Positive":
        rationale = "The news appears positive, suggesting favorable events or results for the company."
    elif sentiment == "Negative":
        rationale = "The news appears negative, indicating potential challenges or poor performance."
    else:
        rationale = "The news is neutral, likely a factual report without strong sentiment."

    insight_card = f"""
    ---
    💡 **Insight Generated**
    ---
    - **Company:** {primary_company_name} ({primary_ticker})
    - **Impact:** {sentiment}
    - **Source:** "{article_title}"
    - **Rationale:** {rationale}
    """
    return insight_card.strip()