import os
import json
from groq import Groq # Import the new library
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create a Groq client, which automatically uses the key from the .env file
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

PROMPT = """
You are an expert financial analyst AI for the Indian stock market. Your task is to read the following news article and identify all publicly-listed Indian companies mentioned.

For each company you identify, provide its official NSE stock ticker symbol.

Instructions:
- Your response must be ONLY a single, valid JSON object, with no extra text, explanations, or markdown formatting like ```json.
- The JSON object should have company names as keys and ticker symbols as values.
- Ignore generic market terms like BSE, NSE, Sensex, and Nifty.
- If you are not highly confident about a ticker for a mentioned company, omit it.

Here is the article text:
---
{text}
---
"""

def get_tickers_from_text(text):
    """
    Uses the Groq API with Llama 3 to extract companies and tickers from text.
    """
    if not os.getenv("GROQ_API_KEY"):
        print("🔴 FATAL ERROR: Groq API Key not found. Please check your .env file.")
        return {}

    print("✅ Groq API Key loaded. Contacting Groq API for analysis...")

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": PROMPT.format(text=text),
                }
            ],
            # We use Llama 3, which is excellent and fast
            model="llama3-8b-8192",
            temperature=0.0, # Low temperature for factual, deterministic output
            response_format={"type": "json_object"}, # Force JSON output
        )

        raw_response_text = chat_completion.choices[0].message.content
        print(f"DEBUG: Raw API Response:\n---\n{raw_response_text}\n---")

        ticker_map = json.loads(raw_response_text)
        return ticker_map

    except Exception as e:
        print(f"🔴 An unexpected error occurred during the Groq API call: {e}")
        return {}