# core_nlp.py
import os
import logging
from dotenv import load_dotenv
from groq import Groq
from config import GROQ_MODEL

load_dotenv()
try:
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key: raise ValueError("GROQ_API_KEY not found.")
    client = Groq(api_key=groq_api_key)
except Exception as e:
    logging.error(f"Core NLP: Failed to initialize Groq client: {e}")
    client = None

def analyze_sentiment_core(text: str) -> dict:
    if not client or not text: return {"sentiment": "Neutral", "confidence": 0.5}
    system_prompt = "You are a financial sentiment analysis expert. Respond with only a single word: Positive, Negative, or Neutral."
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": text[:1500]}],
            model=GROQ_MODEL, temperature=0.0, max_tokens=10,
        )
        response_text = chat_completion.choices[0].message.content.strip().capitalize()
        if "Positive" in response_text: sentiment = "Positive"
        elif "Negative" in response_text: sentiment = "Negative"
        else: sentiment = "Neutral"
        return {"sentiment": sentiment, "confidence": 0.9}
    except Exception as e:
        logging.error(f"Core sentiment analysis failed: {e}"); return {"sentiment": "Neutral", "confidence": 0.5}

def classify_event_type_core(text: str) -> str:
    if not client: return "General News"
    candidate_labels = "Earnings Report, Merger or Acquisition, Analyst Update, Product Launch, Legal or Regulatory Issue, Partnership, Executive Change, or General News"
    system_prompt = f"Classify the headline into one of these categories: {candidate_labels}. Respond with only the category name."
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": f"'{text}'"}],
            model=GROQ_MODEL, temperature=0.0, max_tokens=20,
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Core event classification failed: {e}"); return "General News"
    