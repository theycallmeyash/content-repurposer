import logging
import praw
from datetime import datetime
from typing import List, Dict, Optional
import json
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrendScraperV2:
    """
    Hybrid Trend System:
    1. Manual Input (Primary): User pastes trends from Twitter/LinkedIn
    2. Reddit (Automated): Free, reliable API for supplementary trends
    3. Local Cache: Stores trends to avoid re-fetching
    """
    
    def __init__(self, cache_file: str = "data/trends_cache.json"):
        self.cache_file = cache_file
        self.trends_cache = self._load_cache()
        
        # Reddit API (no auth needed for read-only)
        try:
            self.reddit = praw.Reddit(
                client_id="your_client_id_here",  # User will need to create Reddit app
                client_secret="your_client_secret_here",
                user_agent="ContentRepurposer/1.0"
            )
        except Exception as e:
            logger.warning(f"Reddit API not configured: {e}")
            self.reddit = None

    def _load_cache(self) -> Dict:
        """Load cached trends from file"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except:
                return {"manual": [], "reddit": [], "last_updated": None}
        return {"manual": [], "reddit": [], "last_updated": None}

    def _save_cache(self):
        """Save trends to cache"""
        os.makedirs(os.path.dirname(self.cache_file) if os.path.dirname(self.cache_file) else ".", exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump(self.trends_cache, f, indent=2)

    def add_manual_trends(self, trends: List[str], source: str = "manual"):
        """
        Add trends manually (from Twitter/LinkedIn/etc.)
        :param trends: List of trend keywords
        :param source: Source platform (e.g., "twitter", "linkedin")
        """
        logger.info(f"Adding {len(trends)} manual trends from {source}")
        
        for keyword in trends:
            trend_entry = {
                "keyword": keyword.strip(),
                "source": source,
                "timestamp": datetime.now().isoformat(),
                "type": "manual"
            }
            self.trends_cache["manual"].append(trend_entry)
        
        self._save_cache()
        logger.info(f"Successfully added {len(trends)} trends to cache")

    def get_reddit_trends(self, subreddits: List[str] = ["technology", "programming", "startups"], limit: int = 10) -> List[Dict]:
        """
        Fetch trending posts from Reddit (Free & Reliable)
        :param subreddits: List of subreddits to monitor
        :param limit: Number of hot posts per subreddit
        """
        if not self.reddit:
            logger.warning("Reddit API not configured. Using mock data.")
            return [
                {"keyword": "AI Agents", "source": "reddit_mock", "subreddit": "technology", "timestamp": datetime.now().isoformat()},
                {"keyword": "Startup Funding", "source": "reddit_mock", "subreddit": "startups", "timestamp": datetime.now().isoformat()}
            ]
        
        trends = []
        logger.info(f"Fetching Reddit trends from: {subreddits}")
        
        try:
            for sub_name in subreddits:
                subreddit = self.reddit.subreddit(sub_name)
                for post in subreddit.hot(limit=limit):
                    trends.append({
                        "keyword": post.title,
                        "source": "reddit",
                        "subreddit": sub_name,
                        "score": post.score,
                        "url": f"https://reddit.com{post.permalink}",
                        "timestamp": datetime.now().isoformat()
                    })
            
            self.trends_cache["reddit"] = trends
            self.trends_cache["last_updated"] = datetime.now().isoformat()
            self._save_cache()
            
            logger.info(f"Fetched {len(trends)} Reddit trends")
            return trends
            
        except Exception as e:
            logger.error(f"Error fetching Reddit trends: {e}")
            return []

    def get_all_trends(self) -> List[Dict]:
        """
        Get all trends (manual + automated)
        """
        all_trends = []
        all_trends.extend(self.trends_cache.get("manual", []))
        all_trends.extend(self.trends_cache.get("reddit", []))
        return all_trends

    def clear_cache(self):
        """Clear all cached trends"""
        self.trends_cache = {"manual": [], "reddit": [], "last_updated": None}
        self._save_cache()
        logger.info("Trends cache cleared")


if __name__ == "__main__":
    # Test
    scraper = TrendScraperV2()
    
    # Simulate manual input from Twitter/LinkedIn
    print("\n--- Adding Manual Trends ---")
    scraper.add_manual_trends([
        "AI Agents 2026",
        "LLM Fine-tuning",
        "Startup Growth Hacks"
    ], source="twitter")
    
    scraper.add_manual_trends([
        "B2B SaaS Trends",
        "Remote Work Culture"
    ], source="linkedin")
    
    # Fetch Reddit trends
    print("\n--- Reddit Trends ---")
    reddit_trends = scraper.get_reddit_trends()
    print(json.dumps(reddit_trends[:3], indent=2))
    
    # Get all trends
    print("\n--- All Trends ---")
    all_trends = scraper.get_all_trends()
    print(f"Total trends: {len(all_trends)}")
    for t in all_trends[:5]:
        print(f"  - {t['keyword']} (from {t['source']})")
