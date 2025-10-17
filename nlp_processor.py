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

# Load NSE mapping (official_name -> ticker)
NSE_TICKER_MAP = load_nse_tickers() or {}

# Build a normalized index for fast exact/alias lookup:
# normalized_name -> (official_name, ticker)
def _build_normalized_index(nse_map: dict):
    idx = {}
    for official_name, ticker in nse_map.items():
        # normalized official: lowercase, punctuation -> spaces
        norm = re.sub(r'[^\w\s]', ' ', official_name).lower().strip()
        if norm:
            idx[norm] = (official_name, ticker)
        # also add a version without common suffixes (ltd/limited/inc/...)
        short = re.sub(r'\b(limited|ltd|inc|corporation|corp|llp|llc|pvt|private|company)\b', '', norm).strip()
        if short:
            idx.setdefault(short, (official_name, ticker))
    return idx

NORMALIZED_INDEX = _build_normalized_index(NSE_TICKER_MAP)

# Blocklist normalized (lowercase, punctuation removed)
BLOCKLIST = {re.sub(r'[^\w\s]', ' ', e).lower().strip() for e in (ENTITY_BLOCKLIST or [])}

_sensible_pattern = re.compile(r'^[\w\s.&-]+$')  # allow letters, numbers, spaces, dot, ampersand, dash, underscore

def _normalize_text(s: str) -> str:
    return re.sub(r'[^\w\s]', ' ', s).lower().strip()

def extract_tickers(text: str) -> dict:
    """Extracts validated tickers using spaCy NER + fallback token/ngram + fuzzy matching.
    Returns a dict: {official_name: {'ticker': ticker, 'ner_name': matched_span, 'score': score}}.
    """
    if not text or not NSE_TICKER_MAP:
        return {}

    found_tickers = {}

    # 1) Try spaCy NER if available to get ORG entities
    ner_candidates = set()
    if nlp:
        try:
            doc = nlp(text)
            for ent in doc.ents:
                if ent.label_ == "ORG":
                    cand = ent.text.strip()
                    if cand and _sensible_pattern.match(cand) and len(cand) > 1:
                        ner_candidates.add(cand)
        except Exception as e:
            logging.exception("spaCy failed during NER; falling back to token scan. Err: %s", e)
            ner_candidates = set()

    # 2) Token / n-gram scan fallback & to catch single-word mentions + acronyms
    # Tokenize using a regex so it works even if spaCy unavailable
    tokens = re.findall(r"\b[A-Za-z0-9&\.-]+\b", text)
    # Add unigram tokens that look like company names or acronyms
    for t in tokens:
        if len(t) < 2:
            continue
        # keep uppercase acronyms, capitalized words, and alphabetic words (e.g., Infosys)
        if t.isupper() or (t[0].isupper() and t[1:].islower()) or t.isalpha():
            ner_candidates.add(t)

    # Sliding window ngrams (2..4 tokens) to catch multiword company mentions like "State Bank of India"
    max_n = 4
    for n in range(2, max_n + 1):
        for i in range(len(tokens) - n + 1):
            span = " ".join(tokens[i : i + n])
            if len(span) > 2:
                ner_candidates.add(span)

    # Normalize and remove blocklisted entries
    ner_candidates = {cand for cand in ner_candidates if _normalize_text(cand) not in BLOCKLIST}

    # Helper: try exact normalized lookup first, then fuzzy match
    def _lookup_best_match(ner_name: str):
        norm = _normalize_text(ner_name)
        # exact normalized match in index
        if norm in NORMALIZED_INDEX:
            official_name, ticker = NORMALIZED_INDEX[norm]
            return official_name, ticker, 100  # perfect score

        # acronym exact match attempt: check NSE_TICKER_MAP keys for a direct match (case-insensitive)
        if len(ner_name) <= 5 and re.fullmatch(r'[A-Za-z]+', ner_name):
            for official_name, ticker in NSE_TICKER_MAP.items():
                if official_name.strip().lower() == ner_name.strip().lower():
                    return official_name, ticker, 100

        # fallback: fuzzy match across NSE_TICKER_MAP
        best_name, best_ticker, best_score = None, None, 0
        for official_name, ticker in NSE_TICKER_MAP.items():
            score = fuzz.token_set_ratio(ner_name.lower(), official_name.lower())
            if score > best_score:
                best_score = score
                best_name = official_name
                best_ticker = ticker
            elif score == best_score and best_name and len(official_name) < len(best_name):
                # prefer shorter official name on ties
                best_name, best_ticker = official_name, ticker
        return best_name, best_ticker, best_score

    # Evaluate each candidate and add to found_tickers if passes threshold
    for ner_name in ner_candidates:
        if not ner_name or len(ner_name.strip()) <= 1:
            continue
        if not _sensible_pattern.match(ner_name):
            continue

        official_name, ticker, score = _lookup_best_match(ner_name)
        if official_name and score and score >= FUZZY_MATCH_THRESHOLD:
            prev = found_tickers.get(official_name)
            # If we've already found this official_name, keep the one with better score
            if not prev or score > prev.get('score', 0):
                found_tickers[official_name] = {
                    'ticker': ticker,
                    'ner_name': ner_name,
                    'score': score
                }
                logging.info("Validated ticker: '%s' -> %s (Match: '%s', score=%s)", ner_name, ticker, official_name, score)

    return found_tickers

def extract_key_figures(text: str) -> dict:
    """Uses spaCy to extract and prioritize key numerical figures."""
    if not nlp or not text:
        return {}

    # Using spaCy doc for entity detection
    try:
        doc = nlp(text)
    except Exception as e:
        logging.exception("spaCy failed while parsing text for key figures: %s", e)
        return {}

    figures = {}

    LIMIT_OTHER_FIGURES = 3
    other_percents, other_monies = [], []

    for ent in doc.ents:
        # context window of up to 7 tokens before/after the entity
        context_window = doc[max(0, ent.start - 7):min(len(doc), ent.end + 7)].text.lower()

        if ent.label_ == "PERCENT":
            if "profit" in context_window:
                figures['profit_change_percent'] = ent.text
            elif "revenue" in context_window or "topline" in context_window:
                figures['revenue_change_percent'] = ent.text
            elif len(other_percents) < LIMIT_OTHER_FIGURES:
                other_percents.append(ent.text)

        elif ent.label_ == "MONEY":
            low_ctx = context_window
            if "profit" in low_ctx or "pat" in low_ctx:
                figures['profit_amount'] = ent.text
            elif "revenue" in low_ctx:
                figures['revenue_amount'] = ent.text
            elif "deal" in low_ctx or "wins" in low_ctx or "order" in low_ctx:
                figures['deal_size'] = ent.text
            elif len(other_monies) < LIMIT_OTHER_FIGURES:
                other_monies.append(ent.text)

    if other_percents:
        figures['other_noteworthy_percents'] = other_percents
    if other_monies:
        figures['other_noteworthy_figures'] = other_monies

    return figures
