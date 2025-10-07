# inference_engine.py
import os
import requests
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
# The specific URL for the FinBERT model on Hugging Face's Inference API
API_URL = "https://api-inference.huggingface.co/models/ProsusAI/finbert"
API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")
HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}

def analyze_sentiment(text: str) -> dict:
    """
    Analyzes text sentiment by calling the Hugging Face FinBERT model.
    Returns a dictionary compatible with the dashboard.
    """
    # Defensive checks
    if not API_TOKEN:
        logging.warning("Hugging Face API token not found. Defaulting to Neutral.")
        return {"sentiment": "Neutral", "confidence": 0.0}
    if not text or not text.strip():
        logging.info("Sentiment analysis skipped: Input text is empty.")
        return {"sentiment": "Neutral", "confidence": 0.0}

    # API payload
    payload = {
        "inputs": text,
        "options": {"wait_for_model": True}
    }
    
    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        results = response.json()[0]
        
        # Find the label with the highest score
        best_result = max(results, key=lambda x: x['score'])
        
        # **FIX:** Return a dictionary instead of just a string
        return {
            "sentiment": best_result['label'].capitalize(),
            "confidence": best_result['score']
        }
        
    except requests.RequestException as e:
        logging.error(f"API call failed: {e}")
        return {"sentiment": "Neutral", "confidence": 0.0} # Return a default dict
    except (KeyError, IndexError) as e:
        logging.error(f"Failed to parse API response: {e}")
        return {"sentiment": "Neutral", "confidence": 0.0} # Return a default dict

def generate_insight(article_title: str, linked_tickers: dict, sentiment_result: dict) -> str:
    """
    Combines all gathered information into a final insight.
    """
    if not linked_tickers:
        return "No insights generated as no tickers were found."

    # **FIX:** Get the sentiment label from the dictionary
    sentiment = sentiment_result.get("sentiment", "Neutral")
    primary_company_name = list(linked_tickers.keys())[0]
    primary_ticker = linked_tickers[primary_company_name]
    
    if sentiment == "Positive":
        rationale = "The news appears positive, suggesting favorable events or results."
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