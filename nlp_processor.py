import spacy
import logging
from ticker_utils import load_nse_tickers
from thefuzz import fuzz
import re

# --- INITIALIZATION ---
try:
    nlp = spacy.load("en_core_web_lg")
    logging.info("spaCy NER model loaded successfully.")
except OSError:
    logging.error("spaCy model 'en_core_web_lg' not found. Please run 'python -m spacy download en_core_web_lg'")
    nlp = None

NSE_TICKER_MAP = load_nse_tickers()

# A blocklist of non-tradable entities that are often in the news
ENTITY_BLOCKLIST = {
    # Private Companies
    'swiggy', 'zerodha', 'byju\'s', 'razorpay', 'cred', 
    'phonepe', 'ola', 'oyo', 'pine labs', 'flipkart',
    # Governmental / Regulatory Bodies
    'reserve bank of india', 'rbi',
    'securities and exchange board of india', 'sebi',
    'ministry of finance', 'government of india'
}
# --------------------


def extract_tickers(text: str) -> dict:
    """
    Extracts validated NSE tickers from text using a multi-stage, robust process:
    1.  NER to find organization names.
    2.  Pre-filtering to remove junk and blocklisted entities.
    3.  Intelligent fuzzy matching with tie-breaking to find the best match.
    """
    if not nlp or not NSE_TICKER_MAP:
        return {}

    doc = nlp(text)
    potential_companies_raw = {ent.text.strip() for ent in doc.ents if ent.label_ == "ORG"}
    if not potential_companies_raw: return {}

    # 1. Pre-filter junk strings from corrupted scrapes
    sensible_pattern = re.compile(r'^[a-zA-Z0-9\s.&-]+$')
    potential_companies = {
        name for name in potential_companies_raw if sensible_pattern.match(name) and len(name) > 2
    }
    if not potential_companies: return {}
    
    logging.info(f"NER model found potential organizations: {potential_companies}")

    found_tickers = {}
    
    for ner_name in potential_companies:
        # 2. Filter out known private/non-tradable entities
        if ner_name.lower() in ENTITY_BLOCKLIST:
            logging.warning(f"'{ner_name}' is on the entity blocklist. Skipping.")
            continue

        best_match_name, best_match_ticker, highest_score = (None, None, 0)
        
        # 3. Find the best possible match using an intelligent scoring algorithm
        for official_name, ticker in NSE_TICKER_MAP.items():
            score = fuzz.token_set_ratio(ner_name.lower(), official_name.lower())
            
            if score > highest_score:
                highest_score = score
                best_match_name = official_name
                best_match_ticker = ticker
            # 4. In case of a tied score, prefer the shorter, more fundamental match
            elif score == highest_score and best_match_name and len(official_name) < len(best_match_name):
                best_match_name = official_name
                best_match_ticker = ticker
        
        if highest_score > 90:
            # 5. Return a rich dictionary with all necessary info for downstream use
            found_tickers[best_match_name.title()] = {
                'ticker': best_match_ticker,
                'ner_name': ner_name 
            }
            logging.info(f"Validated ticker: '{ner_name}' -> {best_match_ticker} (Best match: '{best_match_name.title()}' at {highest_score}% similarity)")

    return found_tickers

# In nlp_processor.py

# In nlp_processor.py

def extract_key_figures(text: str) -> dict:
    """
    Uses spaCy to extract and prioritize key numerical figures.
    """
    if not nlp: return {}

    doc = nlp(text)
    figures = {}
    
    # --- NEW: Limit how many "other" figures we collect to reduce noise ---
    LIMIT_OTHER_FIGURES = 3
    other_percents = []
    other_monies = []

    for ent in doc.ents:
        context_window = doc[max(0, ent.start - 7):min(len(doc), ent.end + 7)].text.lower()
        
        if ent.label_ == "PERCENT":
            # Prioritize the most important figures
            if "profit" in context_window:
                figures['profit_change_percent'] = ent.text
            elif "revenue" in context_window or "topline" in context_window:
                figures['revenue_change_percent'] = ent.text
            elif "nii" in context_window:
                figures['nii_change_percent'] = ent.text
            elif "margin" in context_window:
                figures['margin_percent'] = ent.text
            # Collect a limited number of other percentages
            elif len(other_percents) < LIMIT_OTHER_FIGURES:
                other_percents.append(ent.text)
                
        elif ent.label_ == "MONEY":
            if "profit" in context_window or "pat" in context_window:
                figures['profit_amount'] = ent.text
            elif "revenue" in context_window:
                figures['revenue_amount'] = ent.text
            elif "deal" in context_window or "wins" in context_window:
                figures['deal_size'] = ent.text
            # Collect a limited number of other monetary values
            elif len(other_monies) < LIMIT_OTHER_FIGURES:
                other_monies.append(ent.text)
    
    # Only add the "other" lists if they contain data
    if other_percents:
        figures['other_noteworthy_percents'] = other_percents
    if other_monies:
        figures['other_noteworthy_figures'] = other_monies
                
    return figures