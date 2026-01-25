from data_engine.twitter_scraper import TwitterScraper
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_trends():
    scraper = TwitterScraper()
    
    print("Testing get_trends with default WOEID (Global)...")
    try:
        trends, error = scraper.get_trends(woeid=1)
        if error:
            print(f"Error: {error}")
        else:
            print(f"Success! Fetched {len(trends)} trends.")
            if trends:
                print(f"Top trend: {trends[0]['keyword']} ({trends[0]['volume']})")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_trends()
