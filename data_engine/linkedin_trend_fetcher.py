"""
LinkedIn Trend Fetcher
Fetches trending topics, posts, and hashtags from LinkedIn using official APIs.

Supports multiple API providers:
1. LinkedIn Official API (Recommended - Free tier available)
2. RapidAPI LinkedIn Data API (Easier setup)
3. Apify LinkedIn Scraper (Pre-built scraper)
"""
import logging
import requests
from datetime import datetime
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
import json

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LinkedInTrendFetcher:
    """
    Fetches trending content from LinkedIn using various API providers.
    Falls back to curated trends if APIs are unavailable.
    """
    
    def __init__(self, api_provider: str = "official"):
        """
        Initialize the LinkedIn trend fetcher.
        
        :param api_provider: API provider to use ('official', 'rapidapi', 'apify')
        """
        self.api_provider = api_provider
        
        # Load API credentials from environment
        self.linkedin_access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
        self.rapidapi_key = os.getenv('RAPIDAPI_KEY')
        self.apify_token = os.getenv('APIFY_TOKEN')
        
        if not self._has_credentials():
            logger.warning(f"No credentials found for {api_provider}. Will use fallback trends.")
    
    def _has_credentials(self) -> bool:
        """Check if required credentials are available for the selected provider."""
        if self.api_provider == "official":
            return bool(self.linkedin_access_token)
        elif self.api_provider == "rapidapi":
            return bool(self.rapidapi_key)
        elif self.api_provider == "apify":
            return bool(self.apify_token)
        return False
    
    def get_trending_posts_official(self, limit: int = 20) -> List[Dict]:
        """
        Fetch trending posts using LinkedIn Official API.
        
        :param limit: Number of posts to fetch
        :return: List of trending posts
        """
        if not self.linkedin_access_token:
            logger.warning("LinkedIn access token not configured.")
            return self._get_fallback_trends()
        
        logger.info("Fetching LinkedIn trends via Official API...")
        
        try:
            # LinkedIn API endpoint for organization posts
            # Note: This requires proper OAuth setup and organization access
            url = "https://api.linkedin.com/v2/shares"
            
            headers = {
                "Authorization": f"Bearer {self.linkedin_access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0"
            }
            
            params = {
                "q": "owners",
                "count": limit
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            trends = []
            
            # Parse LinkedIn API response
            if "elements" in data:
                for post in data["elements"]:
                    text = post.get("text", {}).get("text", "")
                    if text:
                        # Extract hashtags
                        import re
                        hashtags = re.findall(r'#(\w+)', text)
                        
                        trends.append({
                            "keyword": text[:100] + "..." if len(text) > 100 else text,
                            "hashtags": hashtags,
                            "source": "linkedin_official",
                            "engagement": post.get("totalShareStatistics", {}).get("likeCount", 0),
                            "timestamp": datetime.now().isoformat()
                        })
            
            logger.info(f"✅ Fetched {len(trends)} LinkedIn trends")
            return trends
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.error("LinkedIn API authentication failed. Check your access token.")
            else:
                logger.error(f"LinkedIn API error: {e}")
            return self._get_fallback_trends()
        except Exception as e:
            logger.error(f"Error fetching LinkedIn trends: {e}")
            return self._get_fallback_trends()
    
    def get_trending_posts_rapidapi(self, limit: int = 20) -> List[Dict]:
        """
        Fetch trending posts using RapidAPI LinkedIn Data API.
        
        :param limit: Number of posts to fetch
        :return: List of trending posts
        """
        if not self.rapidapi_key:
            logger.warning("RapidAPI key not configured.")
            return self._get_fallback_trends()
        
        logger.info("Fetching LinkedIn trends via RapidAPI...")
        
        try:
            # RapidAPI LinkedIn endpoint (example - adjust based on actual API)
            url = "https://linkedin-data-api.p.rapidapi.com/get-trending-posts"
            
            headers = {
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": "linkedin-data-api.p.rapidapi.com"
            }
            
            params = {
                "limit": limit,
                "category": "all"
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            trends = []
            
            # Parse RapidAPI response (structure varies by API)
            if "data" in data:
                for post in data["data"]:
                    trends.append({
                        "keyword": post.get("text", "")[:100],
                        "author": post.get("author", {}).get("name", ""),
                        "source": "linkedin_rapidapi",
                        "engagement": post.get("likes", 0) + post.get("comments", 0),
                        "url": post.get("url", ""),
                        "timestamp": datetime.now().isoformat()
                    })
            
            logger.info(f"✅ Fetched {len(trends)} LinkedIn trends via RapidAPI")
            return trends
            
        except Exception as e:
            logger.error(f"RapidAPI error: {e}")
            return self._get_fallback_trends()
    
    def get_trending_posts_apify(self, limit: int = 20) -> List[Dict]:
        """
        Fetch trending posts using Apify LinkedIn Scraper.
        
        :param limit: Number of posts to fetch
        :return: List of trending posts
        """
        if not self.apify_token:
            logger.warning("Apify token not configured.")
            return self._get_fallback_trends()
        
        logger.info("Fetching LinkedIn trends via Apify...")
        
        try:
            # Apify API endpoint
            url = f"https://api.apify.com/v2/acts/apify~linkedin-profile-scraper/runs"
            
            headers = {
                "Authorization": f"Bearer {self.apify_token}",
                "Content-Type": "application/json"
            }
            
            # Apify run input
            payload = {
                "startUrls": [{"url": "https://www.linkedin.com/feed/"}],
                "maxResults": limit
            }
            
            # Start the scraper
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            run_data = response.json()
            
            run_id = run_data.get("data", {}).get("id")
            
            if not run_id:
                raise Exception("Failed to start Apify scraper")
            
            # Wait for results (simplified - in production, use webhooks)
            import time
            time.sleep(10)  # Wait for scraper to complete
            
            # Get results
            results_url = f"https://api.apify.com/v2/acts/apify~linkedin-profile-scraper/runs/{run_id}/dataset/items"
            results_response = requests.get(results_url, headers=headers, timeout=15)
            results_response.raise_for_status()
            results = results_response.json()
            
            trends = []
            
            for item in results[:limit]:
                trends.append({
                    "keyword": item.get("text", "")[:100],
                    "author": item.get("authorName", ""),
                    "source": "linkedin_apify",
                    "engagement": item.get("reactions", 0),
                    "timestamp": datetime.now().isoformat()
                })
            
            logger.info(f"✅ Fetched {len(trends)} LinkedIn trends via Apify")
            return trends
            
        except Exception as e:
            logger.error(f"Apify error: {e}")
            return self._get_fallback_trends()
    
    def _get_fallback_trends(self) -> List[Dict]:
        """
        Return curated LinkedIn-style professional trends.
        Updated manually to reflect current B2B/professional topics.
        """
        logger.info("Using curated LinkedIn trends (fallback)...")
        return [
            {
                "keyword": "AI in Enterprise: How Companies Are Scaling LLMs",
                "hashtags": ["AI", "Enterprise", "LLM"],
                "source": "curated_linkedin",
                "engagement": 1250,
                "timestamp": datetime.now().isoformat()
            },
            {
                "keyword": "The Future of Remote Work: Hybrid Models in 2026",
                "hashtags": ["RemoteWork", "FutureOfWork", "Hybrid"],
                "source": "curated_linkedin",
                "engagement": 980,
                "timestamp": datetime.now().isoformat()
            },
            {
                "keyword": "B2B SaaS Growth Strategies for Startups",
                "hashtags": ["SaaS", "B2B", "Startups"],
                "source": "curated_linkedin",
                "engagement": 875,
                "timestamp": datetime.now().isoformat()
            },
            {
                "keyword": "Leadership Lessons: Building High-Performance Teams",
                "hashtags": ["Leadership", "TeamBuilding", "Management"],
                "source": "curated_linkedin",
                "engagement": 1100,
                "timestamp": datetime.now().isoformat()
            },
            {
                "keyword": "Data Privacy Regulations: What Businesses Need to Know",
                "hashtags": ["DataPrivacy", "Compliance", "GDPR"],
                "source": "curated_linkedin",
                "engagement": 720,
                "timestamp": datetime.now().isoformat()
            },
            {
                "keyword": "Sustainable Business Practices: ESG in 2026",
                "hashtags": ["Sustainability", "ESG", "GreenBusiness"],
                "source": "curated_linkedin",
                "engagement": 650,
                "timestamp": datetime.now().isoformat()
            },
            {
                "keyword": "Product-Led Growth: Lessons from Top SaaS Companies",
                "hashtags": ["ProductLedGrowth", "PLG", "SaaS"],
                "source": "curated_linkedin",
                "engagement": 890,
                "timestamp": datetime.now().isoformat()
            },
            {
                "keyword": "The Rise of AI Agents in Customer Service",
                "hashtags": ["AIAgents", "CustomerService", "Automation"],
                "source": "curated_linkedin",
                "engagement": 1050,
                "timestamp": datetime.now().isoformat()
            }
        ]
    
    def get_all_trends(self, limit: int = 20) -> List[Dict]:
        """
        Fetch trends using the configured API provider.
        
        :param limit: Number of trends to fetch
        :return: List of trending topics
        """
        if self.api_provider == "official":
            return self.get_trending_posts_official(limit=limit)
        elif self.api_provider == "rapidapi":
            return self.get_trending_posts_rapidapi(limit=limit)
        elif self.api_provider == "apify":
            return self.get_trending_posts_apify(limit=limit)
        else:
            logger.warning(f"Unknown API provider: {self.api_provider}. Using fallback.")
            return self._get_fallback_trends()


if __name__ == "__main__":
    print("\n" + "="*70)
    print("LINKEDIN TREND FETCHER")
    print("="*70)
    print("\n📋 Supported API Providers:")
    print("  1. LinkedIn Official API (LINKEDIN_ACCESS_TOKEN)")
    print("  2. RapidAPI (RAPIDAPI_KEY)")
    print("  3. Apify (APIFY_TOKEN)")
    print("\n⚠️  Add credentials to .env file to fetch real data")
    print("="*70 + "\n")
    
    # Test with fallback (no credentials)
    fetcher = LinkedInTrendFetcher(api_provider="official")
    trends = fetcher.get_all_trends(limit=10)
    
    print(f"\n✅ Fetched {len(trends)} LinkedIn trends:\n")
    
    for i, trend in enumerate(trends, 1):
        engagement = trend.get('engagement', 'N/A')
        hashtags = trend.get('hashtags', [])
        hashtag_str = " ".join([f"#{tag}" for tag in hashtags[:3]]) if hashtags else ""
        
        print(f"{i}. {trend['keyword']}")
        print(f"   💬 Engagement: {engagement} | 🏷️  {hashtag_str}")
        print(f"   📍 Source: {trend['source']}\n")
    
    print(f"💡 TIP: Add API credentials to .env to fetch real LinkedIn trends")
