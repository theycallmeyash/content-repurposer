from data_engine.twitter_scraper import TwitterScraper
import asyncio
import logging

logging.basicConfig(level=logging.INFO)

def check_date_format():
    scraper = TwitterScraper()
    print("Fetching one tweet to check date format...")
    # Fetch 1 tweet
    tweets, error = scraper.search_tweets("python", limit=1)
    
    if tweets:
        t = tweets[0]
        print(f"Sample Tweet Date: '{t['created_at']}'")
        print(f"Type: {type(t['created_at'])}")
    else:
        print(f"No tweets found. Error: {error}")

if __name__ == "__main__":
    check_date_format()
