# nlp_processor.py
import os
import json
import logging
import re
from groq import Groq
from dotenv import load_dotenv
from ticker_mapping import KNOWN_COMPANIES

# --- Setup ---
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# UPDATED: The prompt is now much stricter to prevent non-JSON output.
PROMPT_INSTRUCTIONS = """
You are an expert financial analyst AI for the Indian stock market. Your task is to read the following news article and identify all publicly-listed Indian companies mentioned.

Instructions:
- Your response MUST be ONLY a single, valid JSON object.
- DO NOT add any notes, explanations, or markdown formatting.
- The JSON object should be a dictionary where keys are the company names and values are their official NSE stock ticker symbols.
- If you are not 100% confident about a ticker, or if a company is not listed, DO NOT include it in the JSON.
- If no publicly-listed Indian companies are found, return an empty JSON object {}.

News:
"""

def extract_tickers(text):
    """
    Finds tickers using a robust "LLM-first, local validation" approach.
    """
    logging.info("🤖 Using LLM to perform primary analysis...")
    try:
        if not client.api_key:
            logging.error("❌ Groq API key not found.")
            return {}

        # Construct the prompt via concatenation to be more robust
        full_prompt = PROMPT_INSTRUCTIONS + text

        # --- Step 1: Always call the LLM to get potential companies ---
        response = client.chat.completions.create(
            model="qwen/qwen3-32b",
            messages=[{"role": "user", "content": full_prompt}],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        llm_results = json.loads(content)
        
        if not llm_results:
            logging.warning("LLM returned no companies.")
            return {}
            
        logging.info(f"LLM identified potential tickers: {llm_results}")

        # --- Step 2: Validate LLM results against our known list ---
        # UPDATED: More precise validation logic.
        final_tickers = {}
        validated_companies = []

        # Prioritize longer, more specific matches first
        sorted_llm_results = sorted(llm_results.items(), key=lambda item: len(item[0]), reverse=True)

        for company, ticker in sorted_llm_results:
            # Check if the company found by the LLM is in our trusted list
            for known_company, known_ticker in KNOWN_COMPANIES.items():
                # This ensures "Tata Motors" matches "Tata Motors", but "SBI" doesn't match "SBI Life"
                if company.lower() == known_company.lower():
                    logging.info(f"🎯 Validated LLM result with local map: {known_company}")
                    validated_companies.append((known_company, known_ticker))
        
        # If we have validated companies, return the first one
        if validated_companies:
            first_match = validated_companies[0]
            return {first_match[0]: first_match[1]}

        # If no validated match, trust the first valid result from the LLM
        logging.info("No validated companies found. Trusting the first valid LLM result.")
        if llm_results:
            first_company = next(iter(llm_results))
            first_ticker = llm_results[first_company]
            if first_ticker: # Ensure the ticker is not None
                return {first_company: first_ticker}

        return {}

    except Exception as e:
        logging.error(f"❌ Error during NLP processing: {e}")
        return {}
