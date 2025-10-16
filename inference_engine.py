import os
import logging
from dotenv import load_dotenv
import streamlit as st
from groq import Groq

# --- Configuration ---
load_dotenv()
try:
    # Securely initialize Groq client, checking for local .env file and Streamlit secrets
    groq_api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables or Streamlit secrets.")
    client = Groq(api_key=groq_api_key)
    logging.info("Groq client initialized successfully.")
except Exception as e:
    logging.error(f"Failed to initialize Groq client: {e}")
    client = None

# --- Core Functions Using the Llama 3.1 Model ---

@st.cache_data(ttl="1h")
def analyze_sentiment(text: str) -> dict:
    """Analyzes text sentiment using the high-speed Groq API."""
    if not client or not text or not text.strip():
        return {"sentiment": "Neutral", "confidence": 0.5}
    
    # A more forceful prompt to ensure a single-word response
    system_prompt = "You are a financial sentiment analysis expert. Your task is to analyze the sentiment of the provided text. Respond with only a single word: Positive, Negative, or Neutral."
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text[:1500]} # Truncate text to be safe
            ],
            model="llama-3.1-8b-instant",  # <-- FIX APPLIED: Using the new model
            temperature=0.0,
            max_tokens=10,
        )
        response_text = chat_completion.choices[0].message.content.strip().capitalize()
        
        # Robust parsing: check if the key sentiment word is in the response
        if "Positive" in response_text:
            sentiment = "Positive"
        elif "Negative" in response_text:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"
            
        return {"sentiment": sentiment, "confidence": 0.9} # Assume high confidence for now
        
    except Exception as e:
        logging.error(f"Groq sentiment analysis failed: {e}")
        return {"sentiment": "Neutral", "confidence": 0.5}

@st.cache_data(ttl="1h")
def classify_event_type(text: str) -> str:
    """Classifies the news headline into a predefined event category using Groq."""
    if not client: return "General News"
        
    candidate_labels = "Earnings Report, Merger or Acquisition, Analyst Update, Product Launch, Legal or Regulatory Issue, Partnership, Executive Change, or General News"
    system_prompt = f"You are an expert financial news categorizer. Classify the headline into one of these categories: {candidate_labels}. Respond with only the category name."

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"'{text}'"}
            ],
            model="llama-3.1-8b-instant",  # <-- FIX APPLIED: Using the new model
            temperature=0.0,
            max_tokens=20,
        )
        return chat_completion.choices[0].message.content.strip()
        
    except Exception as e:
        logging.error(f"Groq event classification failed: {e}")
        return "General News"

# --- The generate_insight function remains unchanged ---
def generate_insight(article_title, linked_tickers, sentiment_result):
    sentiment = sentiment_result.get("sentiment", "Neutral")
    company_name = list(linked_tickers.keys())[0]
    ticker = list(linked_tickers.values())[0]
    
    rationale = "The news is neutral, likely a factual report without strong sentiment."
    if sentiment == "Positive":
        rationale = "The news appears positive, suggesting favorable events or results."
    elif sentiment == "Negative":
        rationale = "The news appears negative, indicating potential challenges or poor performance."

    return f"Insight for {company_name} ({ticker}): {rationale} based on '{article_title}'."