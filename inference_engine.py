# inference_engine.py
import streamlit as st
from core_nlp import analyze_sentiment_core, classify_event_type_core

@st.cache_data(ttl="1h")
def analyze_sentiment(text: str) -> dict:
    return analyze_sentiment_core(text)

@st.cache_data(ttl="1h")
def classify_event_type(text: str) -> str:
    return classify_event_type_core(text)

def generate_insight(title: str, linked_tickers: dict, sentiment: dict) -> str:
    """Formats a human-readable insight summary from article data."""
    sentiment_label = sentiment.get("sentiment", "Neutral")
    confidence = sentiment.get("confidence", 0.0)
    confidence_pct = f"{confidence * 100:.0f}%"

    ticker_list = ", ".join(
        f"{data['ticker']}" for data in linked_tickers.values()
    ) if linked_tickers else "N/A"

    sentiment_emoji = {"Positive": "🟢", "Negative": "🔴", "Neutral": "🟡"}.get(sentiment_label, "⚪")

    return (
        f"  Headline : {title}\n"
        f"  Tickers  : {ticker_list}\n"
        f"  Sentiment: {sentiment_emoji} {sentiment_label} (confidence: {confidence_pct})"
    )
