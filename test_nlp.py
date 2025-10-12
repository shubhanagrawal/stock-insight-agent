# test_nlp.py
import logging

# Set logging to INFO to see all messages
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s: %(message)s')

print("--- Testing NLP Processor Initialization ---")

try:
    from nlp_processor import extract_tickers

    print("\n--- Initialization Successful ---")
    
    # Now, let's test it with a sample text
    print("\n--- Testing with Sample Text ---")
    sample_text = "Reliance Industries and IDFC First Bank saw major stock movements today."
    found = extract_tickers(sample_text)
    
    if found:
        print("\n✅ SUCCESS: Tickers extracted successfully!")
        print(found)
    else:
        print("\n❌ WARNING: Tickers were NOT extracted. The function ran but found nothing.")

except Exception as e:
    print(f"\n❌ CRITICAL ERROR during import or initialization: {e}")