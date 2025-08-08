import os
import google.generativeai as genai
from dotenv import load_dotenv
import traceback # We'll use this for a more detailed error message

# --- 1. Load API Key ---
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    print("🔴 FATAL: API Key not found in your .env file.")
else:
    print("✅ API Key successfully loaded from .env file.")
    genai.configure(api_key=API_KEY)
    
    # --- 2. Define a Simple, Neutral Prompt ---
    # We are NOT using financial news to rule out safety filters as the cause.
    simple_prompt = "Explain what a stock market is in one simple sentence."
    print(f"\nAttempting a simple test call to the Gemini API with prompt: '{simple_prompt}'")

    # --- 3. Make the API Call with Detailed Error Catching ---
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        response = model.generate_content(simple_prompt)
        
        print("\n✅ SUCCESS! The API call worked.")
        print("---------------------------------")
        print(f"Response from API: {response.text}")
        print("---------------------------------")
        print("\nThis confirms your API key and connection to Google are working correctly.")

    except Exception as e:
        print("\n🔴 API CALL FAILED. Here is the full, detailed error traceback:")
        print("-------------------------------------------------")
        # This will print the exact line and reason for the failure.
        traceback.print_exc()
        print("-------------------------------------------------")