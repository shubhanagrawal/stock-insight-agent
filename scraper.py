import requests
import feedparser
from newspaper import Article # New import!

# The Economic Times Markets RSS feed
NEWS_FEED_URL = "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"

# Headers to mimic a real browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
}

def fetch_latest_article():
    """
    Fetches the latest article from the RSS feed and returns its
    title, URL, and full text content.
    """
    print("Attempting to fetch RSS feed...")
    try:
        response = requests.get(NEWS_FEED_URL, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            print("RSS feed fetch successful. Parsing feed...")
            feed = feedparser.parse(response.content)
            
            if feed.entries:
                # Get the first article from the feed
                latest_entry = feed.entries[0]
                article_url = latest_entry.link
                
                print(f"Found article: {latest_entry.title}")
                print(f"Fetching full content from: {article_url}")

                # Use newspaper3k to get the full article text
                try:
                    article = Article(article_url)
                    article.download()
                    article.parse()
                    
                    # Return a dictionary with all the info we need
                    return {
                        "title": latest_entry.title,
                        "url": article_url,
                        "text": article.text
                    }
                except Exception as e:
                    print(f"Error fetching full article content with newspaper3k: {e}")
                    return None
            else:
                print("Error: No entries found in the RSS feed.")
                return None
        else:
            print(f"Error: Failed to fetch RSS feed. Status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the network request: {e}")
        return None

if __name__ == "__main__":
    article_data = fetch_latest_article()
    
    if article_data:
        print("\n✅ SUCCESS! Article data extracted.")
        print("------------------------------------")
        print(f"Title: {article_data['title']}")
        print(f"URL: {article_data['url']}")
        print(f"\nText: \n{article_data['text'][:500]}...") # Print first 500 chars of text
    else:
        print("\n❌ Failed to fetch article data.")