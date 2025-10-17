import spacy
import logging
import re
from ticker_utils import load_nse_tickers
from thefuzz import fuzz
from config import FUZZY_MATCH_THRESHOLD, ENTITY_BLOCKLIST

# --- INITIALIZATION ---
try:
    nlp = spacy.load("en_core_web_lg")
except OSError:
    logging.error("spaCy model 'en_core_web_lg' not found. Run 'python -m spacy download en_core_web_lg'")
    nlp = None

NSE_TICKER_MAP = load_nse_tickers()

def extract_tickers(text: str) -> dict:
    """Extracts validated tickers using NER + fallback fuzzy/regex logic."""
    if not NSE_TICKER_MAP:
        return {}

    found_tickers = {}
    potential_companies_raw = set()

    # --- Stage 1: NER extraction (if spaCy model is available) ---
    if nlp:
        doc = nlp(text)
        potential_companies_raw |= {ent.text.strip() for ent in doc.ents if ent.label_ == "ORG"}

    # --- Stage 2: Simple pattern-based extraction (fallback for missed NER) ---
    # capture capitalized words that might be company names
    pattern = re.compile(r'\b([A-Z][a-zA-Z.&\s]{2,})\b')
    potential_companies_raw |= set(pattern.findall(text))

    # --- Filter unwanted patterns ---
    sensible_pattern = re.compile(r'^[a-zA-Z0-9\s.&-]+$')
    potential_companies = {
        name.strip()
        for name in potential_companies_raw
        if sensible_pattern.match(name) and len(name) > 2
    }

    # --- Stage 3: Match each potential name against NSE tickers ---
    for ner_name in potential_companies:
        if ner_name.lower() in ENTITY_BLOCKLIST:
            continue

        best_match_name, best_match_ticker, highest_score = (None, None, 0)

        for official_name, ticker in NSE_TICKER_MAP.items():
            score = fuzz.token_set_ratio(ner_name.lower(), official_name.lower())
            if score > highest_score:
                highest_score, best_match_name, best_match_ticker = score, official_name, ticker
            elif score == highest_score and best_match_name and len(official_name) < len(best_match_name):
                best_match_name, best_match_ticker = official_name, ticker

        if highest_score > FUZZY_MATCH_THRESHOLD:
            found_tickers[best_match_name] = {
                "ticker": best_match_ticker,
                "ner_name": ner_name
            }
            logging.info(f"Validated ticker: '{ner_name}' -> {best_match_ticker} (Match: '{best_match_name}')")

    return found_tickers


def extract_key_figures(text: str) -> dict:
    """Uses spaCy to extract and prioritize key numerical figures."""
    if not nlp:
        return {}

    doc = nlp(text)
    figures = {}

    LIMIT_OTHER_FIGURES = 3
    other_percents, other_monies = [], []

    for ent in doc.ents:
        context_window = doc[max(0, ent.start - 7):min(len(doc), ent.end + 7)].text.lower()

        if ent.label_ == "PERCENT":
            if "profit" in context_window:
                figures["profit_change_percent"] = ent.text
            elif "revenue" in context_window or "topline" in context_window:
                figures["revenue_change_percent"] = ent.text
            elif len(other_percents) < LIMIT_OTHER_FIGURES:
                other_percents.append(ent.text)

        elif ent.label_ == "MONEY":
            if "profit" in context_window or "pat" in context_window:
                figures["profit_amount"] = ent.text
            elif "revenue" in context_window:
                figures["revenue_amount"] = ent.text
            elif "deal" in context_window or "wins" in context_window:
                figures["deal_size"] = ent.text
            elif len(other_monies) < LIMIT_OTHER_FIGURES:
                other_monies.append(ent.text)

    if other_percents:
        figures["other_noteworthy_percents"] = other_percents
    if other_monies:
        figures["other_noteworthy_figures"] = other_monies

    return figures
