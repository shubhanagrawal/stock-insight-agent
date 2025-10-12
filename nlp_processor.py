# nlp_processor.py
import spacy
import logging
from ticker_utils import load_nse_tickers # Import our new loader function

# --- INITIALIZATION ---
# Load the spaCy model once when the module is imported for efficiency
try:
    nlp = spacy.load("en_core_web_lg")
    logging.info("spaCy NER model loaded successfully.")
except OSError:
    logging.error("spaCy model 'en_core_web_lg' not found. Please run 'python -m spacy download en_core_web_lg'")
    nlp = None

# Load the NSE ticker mapping once for efficiency
NSE_TICKER_MAP = load_nse_tickers()
# --------------------


# In your nlp_processor.py file

# In your nlp_processor.py file

def extract_tickers(text: str) -> dict:
    """
    Extracts company names and their validated NSE tickers from text.
    """
    if not nlp or not NSE_TICKER_MAP:
        logging.warning("NLP processor or ticker map not initialized. Skipping extraction.")
        return {}

    # Step 1: Use NER to find potential company names
    doc = nlp(text)
    potential_companies = {ent.text.strip() for ent in doc.ents if ent.label_ == "ORG"}

    if not potential_companies:
        logging.warning("NER model did not find any organizations in the text.")
        return {}
    
    logging.info(f"NER model found potential organizations: {potential_companies}")

    found_tickers = {}

    # --- FIX APPLIED HERE ---
    # We now use a more flexible partial match instead of an exact match.
    for official_name, ticker in NSE_TICKER_MAP.items():
        for ner_name in potential_companies:
            # Check if the NER-found name is a substring of the official name
            if ner_name.lower() in official_name.lower():
                # Use the official name from the CSV for consistency
                found_tickers[official_name.title()] = ticker
                logging.info(f"Validated ticker: {ner_name} -> {ticker} (Matched with '{official_name.title()}')")
                break # Move to the next official name once a match is found
            
    return found_tickers