# inference_engine.py
import streamlit as st
from core_nlp import analyze_sentiment_core, classify_event_type_core

@st.cache_data(ttl="1h")
def analyze_sentiment(text: str) -> dict:
    return analyze_sentiment_core(text)

@st.cache_data(ttl="1h")
def classify_event_type(text: str) -> str:
    return classify_event_type_core(text)
