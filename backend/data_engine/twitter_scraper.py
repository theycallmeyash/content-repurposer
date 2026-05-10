from twikit import Client
import json
import os
import logging
from datetime import datetime, timedelta
import asyncio
import time
from typing import Dict, List, Optional, Tuple, Any
from functools import wraps
import hashlib
from pathlib import Path

logger = logging.getLogger(__name__)

class TwitterScraperCache:
    """Simple in-memory and file-based cache for Twitter data"""
    
    def __init__(self, cache_dir='twitter_cache'):
        self.cache_dir = cache_dir
        self.memory_cache = {}
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_key(self, key: str) -> str:
        """Generate a hash-based cache key"""
        return hashlib.md5(key.encode()).hexdigest()
    
    def get(self, key: str, max_age_seconds: int = 3600) -> Optional[Any]:
        """Get cached data if it exists and is not expired"""
        # Check memory cache first
        if key in self.memory_cache:
            data, timestamp = self.memory_cache[key]
            if time.time() - timestamp < max_age_seconds:
                logger.debug(f"Cache HIT (memory): {key}")
                return data
            else:
                del self.memory_cache[key]
        
        # Check file cache
        cache_key = self._get_cache_key(key)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cached = json.load(f)
                    if time.time() - cached['timestamp'] < max_age_seconds:
                        logger.debug(f"Cache HIT (file): {key}")
                        # Load into memory cache
                        self.memory_cache[key] = (cached['data'], cached['timestamp'])
                        return cached['data']
                    else:
                        os.remove(cache_file)
            except Exception as e:
                logger.warning(f"Cache read error: {e}")
        
        logger.debug(f"Cache MISS: {key}")
        return None
    
    def set(self, key: str, data: Any):
        """Set cached data in both memory and file"""
        timestamp = time.time()
        self.memory_cache[key] = (data, timestamp)
        
        # Also save to file
        cache_key = self._get_cache_key(key)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        try:
            with open(cache_file, 'w') as f:
                json.dump({'data': data, 'timestamp': timestamp}, f)
            logger.debug(f"Cache SET: {key}")
        except Exception as e:
            logger.warning(f"Cache write error: {e}")
    
    def clear(self):
        """Clear all cache"""
        self.memory_cache.clear()
        for file in os.listdir(self.cache_dir):
            if file.endswith('.json'):
                os.remove(os.path.join(self.cache_dir, file))
        logger.info("Cache cleared")


class TwitterScraper:
    def __init__(self):
        project_root = Path(__file__).resolve().parents[2]
        self.cookies_path = os.getenv("TWITTER_COOKIES_PATH", str(project_root / "twitter_cookies.json"))
        self.cache = TwitterScraperCache(cache_dir=str(project_root / "twitter_cache"))
        self.rate_limit_reset = None
        self.request_count = 0
        self.max_requests_per_window = 50  # Conservative limit
        self.window_start = time.time()
    
    def _extract_media_info(self, tweet) -> Dict:
        """Extract media information from a twikit tweet object"""
        media_info = {'has_media': False, 'type': None, 'count': 0}
        try:
            media = getattr(tweet, 'media', None)
            if media and len(media) > 0:
                media_info['has_media'] = True
                media_info['count'] = len(media)
                # Detect type from first media item
                first = media[0]
                media_type = getattr(first, 'type', '') or ''
                if 'video' in media_type.lower() or 'animated_gif' in media_type.lower():
                    media_info['type'] = 'video' if 'video' in media_type.lower() else 'gif'
                else:
                    media_info['type'] = 'image'
        except Exception:
            pass
        return media_info
        
    def _get_client(self):
        """Get a fresh client instance"""
        client = Client('en-US', http2=True)
        return client
    
    def _check_rate_limit(self):
        """Check if we're within rate limits"""
        current_time = time.time()
        
        # Reset counter every 15 minutes
        if current_time - self.window_start > 900:  # 15 minutes
            self.request_count = 0
            self.window_start = current_time
        
        # If we're approaching the limit, wait
        if self.request_count >= self.max_requests_per_window:
            wait_time = 900 - (current_time - self.window_start)
            if wait_time > 0:
                logger.warning(f"Rate limit approaching. Waiting {wait_time:.0f} seconds...")
                time.sleep(wait_time)
                self.request_count = 0
                self.window_start = time.time()
        
        self.request_count += 1
    
    def _retry_with_backoff(self, func, max_retries=3, initial_delay=1):
        """Retry a function with exponential backoff"""
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                
                # Check if it's a rate limit error
                if "429" in str(e) or "rate limit" in str(e).lower():
                    delay = initial_delay * (2 ** attempt) * 2  # Longer delay for rate limits
                    logger.warning(f"Rate limit hit. Retrying in {delay}s... (attempt {attempt + 1}/{max_retries})")
                else:
                    delay = initial_delay * (2 ** attempt)
                    logger.warning(f"Error: {str(e)}. Retrying in {delay}s... (attempt {attempt + 1}/{max_retries})")
                
                time.sleep(delay)
        
        raise Exception(f"Failed after {max_retries} retries")

    def login(self, username, email, password):
        """
        Login to Twitter and save cookies
        """
        async def _login_task():
            client = self._get_client()
            logger.info("Logging in with credentials...")
            await client.login(
                auth_info_1=username,
                auth_info_2=email,
                password=password
            )
            client.save_cookies(self.cookies_path)
            
        try:
            # Check if cookies exist first
            if os.path.exists(self.cookies_path):
                logger.info("Loading existing cookies...")
                return True, "Cookies already exist. Try fetching trends."
            
            asyncio.run(_login_task())
            return True, "Login successful & cookies saved"
            
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return False, f"Login failed: {str(e)}"

    def login_with_manual_cookies(self, cookie_json: str):
        """
        Login using manually pasted cookies JSON
        """
        try:
            # Validate JSON
            cookies_data = json.loads(cookie_json)
            
            # Determine format and normalize to simple dict {name: value}
            final_cookies = {}
            
            if isinstance(cookies_data, list):
                # Browser export format: [{"name": "foo", "value": "bar"}, ...]
                logger.info("Detected list-format cookies (Browser Export)")
                for cookie in cookies_data:
                    if isinstance(cookie, dict) and 'name' in cookie and 'value' in cookie:
                        final_cookies[cookie['name']] = cookie['value']
            elif isinstance(cookies_data, dict):
                 # Simple dict format: {"foo": "bar"}
                 logger.info("Detected dict-format cookies")
                 final_cookies = cookies_data
            else:
                 return False, "Invalid cookie format. Must be a list or dict."

            if not final_cookies:
                return False, "No valid cookies found in the provided JSON."

            # Save as simple dict which httpx/twikit expects
            with open(self.cookies_path, 'w') as f:
                json.dump(final_cookies, f)
                
            logger.info(f"Saved {len(final_cookies)} cookies to {self.cookies_path}")
            
            # Clear cache on new login
            self.cache.clear()
            
            return True, "Cookies imported successfully! Cache cleared. Try fetching trends now."
            
        except json.JSONDecodeError:
            return False, "Invalid JSON format. Please paste a valid JSON object."
        except Exception as e:
            logger.error(f"Manual cookie import failed: {str(e)}")
            return False, f"Import failed: {str(e)}"

    def validate_cookies(self) -> bool:
        """Validate that cookies are still valid"""
        if not os.path.exists(self.cookies_path):
            return False
        
        try:
            # Try a simple API call to validate
            async def _validate():
                import httpx
                with open(self.cookies_path, 'r') as f:
                    saved_cookies = json.load(f)
                
                async with httpx.AsyncClient(http2=True) as http_client:
                    for name, value in saved_cookies.items():
                        http_client.cookies.set(name, value, domain='.x.com')
                    
                    csrf_token = saved_cookies.get('ct0')
                    headers = {
                        'x-csrf-token': csrf_token,
                        'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
                    }
                    
                    # Simple validation call
                    response = await http_client.get(
                        'https://api.x.com/1.1/account/verify_credentials.json',
                        headers=headers
                    )
                    return response.status_code == 200
            
            return asyncio.run(_validate())
        except:
            return False

    def get_trends(self, use_cache=True, cache_ttl=600, woeid=1):
        """
        Fetch current trends with caching
        cache_ttl: Cache time-to-live in seconds (default 10 minutes)
        """
        cache_key = "trends_global"
        
        # Check cache first
        if use_cache:
            cached_data = self.cache.get(cache_key, max_age_seconds=cache_ttl)
            if cached_data:
                logger.info("Returning cached trends")
                return cached_data, None
        
        async def _trends_task():
            try:
                self._check_rate_limit()
                
                client = self._get_client()
                client.load_cookies(self.cookies_path)
                
                logger.info(f"Fetching trends from API using twikit (WOEID: {woeid})...")
                
                # Use twikit to fetch trends
                # Returns a PlaceTrends TypedDict: {'trends': [PlaceTrend], ...}
                result = await client.get_place_trends(woeid)
                
                trends_data = result.get('trends', [])
                
                # Convert PlaceTrend objects to dicts for downstream compatibility
                formatted_trends = []
                for trend in trends_data:
                    formatted_trends.append({
                        'name': trend.name,
                        'tweet_volume': trend.tweet_volume,
                        'url': trend.url,
                        'query': trend.query
                    })
                
                logger.info(f"Fetched {len(formatted_trends)} trends")
                return formatted_trends
                
            except Exception as e:
                import traceback
                logger.error(f"Trends fetch error: {traceback.format_exc()}")
                raise e

        try:
            if not os.path.exists(self.cookies_path):
                 return [], "Not logged in. Please login first."

            def fetch_trends():
                return asyncio.run(_trends_task())
            
            trends = self._retry_with_backoff(fetch_trends)
            
            formatted_trends = []
            
            for trend in trends:
                name = trend.get('name', 'Unknown')
                volume = trend.get('tweet_volume')
                if volume:
                    volume_str = f"{volume:,}"
                else:
                    volume_str = "N/A"
                
                formatted_trends.append({
                    'keyword': name,
                    'volume': volume_str,
                    'domain': 'Trending',
                })
            
            # Cache the results
            if use_cache:
                self.cache.set(cache_key, formatted_trends)

            return formatted_trends, None
            
        except Exception as e:
            logger.error(f"Error fetching trends: {str(e)}")
            if "403" in str(e):
                 return [], "Error 403: Access Denied. Cookies may be invalid. Try logging in again."
            if "429" in str(e):
                 return [], "Error 429: Rate limit exceeded. Please wait a few minutes."
            return [], f"Error fetching trends: {str(e)}"
    
    def search_tweets(self, query, product='Top', limit=20):
        """
        Search for tweets
        product: 'Top', 'Latest', 'Media'
        """
        async def _search_task():
            client = self._get_client()
            client.load_cookies(self.cookies_path)
            
            import re
            user_match = re.search(r'from:([A-Za-z0-9_]+)', query)
            if user_match:
                username = user_match.group(1)
                logger.info(f"Using get_user_tweets fallback for {username}")
                try:
                    user = await client.get_user_by_screen_name(username)
                    tweets_result = await client.get_user_tweets(user.id, 'Tweets')
                    all_tweets = list(tweets_result)
                    
                    filtered_tweets = []
                    exclude_replies = '-filter:replies' in query
                    exclude_retweets = '-filter:retweets' in query
                    
                    while len(filtered_tweets) < limit:
                        for t in all_tweets:
                            is_reply = bool(getattr(t, 'in_reply_to_user_id', None) or getattr(t, 'in_reply_to_status_id', None))
                            is_retweet = t.text.startswith('RT @') if getattr(t, 'text', '') else False
                            
                            if exclude_replies and is_reply: continue
                            if exclude_retweets and is_retweet: continue
                            
                            filtered_tweets.append(t)
                            if len(filtered_tweets) >= limit: break
                            
                        if len(filtered_tweets) >= limit: break
                        try:
                            more_tweets = await tweets_result.next()
                            if not more_tweets: break
                            all_tweets = list(more_tweets)
                        except Exception as e:
                            logger.warning(f"Fallback pagination failed: {e}")
                            break
                    
                    print(f"DEBUG search_tweets: total after fallback filtering = {len(filtered_tweets)} tweets")
                    return filtered_tweets[:limit]
                except Exception as e:
                    logger.warning(f"Fallback get_user_tweets failed: {e}. Trying regular search.")

            # Twikit usually caps count per request at ~20-40
            req_count = min(limit, 40)
            tweets_result = await client.search_tweet(query, product=product, count=req_count)
            
            all_tweets = list(tweets_result)
            print(f"DEBUG search_tweets: initial batch = {len(all_tweets)} tweets")
            
            # Automatically paginate to hit the desired limit
            while len(all_tweets) < limit:
                try:
                    more_tweets = await tweets_result.next()
                    if not more_tweets:
                        break
                    all_tweets.extend(list(more_tweets))
                except Exception as e:
                    logger.warning(f"Failed to fetch next page: {e}")
                    break
                    
            print(f"DEBUG search_tweets: total after pagination = {len(all_tweets)} tweets")
            return all_tweets[:limit]

        try:
             if not os.path.exists(self.cookies_path):
                 return [], "Not logged in. Please login first."
             
             self._check_rate_limit()
             
             def search():
                 return asyncio.run(_search_task())
             
             tweets = self._retry_with_backoff(search)
             print(f"DEBUG search_tweets: raw twikit objects = {len(tweets)}")
             
             results = []
             for tweet in tweets:
                 results.append({
                     'id': tweet.id,
                     'text': tweet.text,
                     'user': {
                        'name': tweet.user.name,
                        'screen_name': tweet.user.screen_name,
                        'verified': tweet.user.is_blue_verified or tweet.user.verified,
                        'followers_count': tweet.user.followers_count,
                        'friends_count': tweet.user.following_count,
                        'statuses_count': tweet.user.statuses_count
                     },
                     'screen_name': tweet.user.screen_name,
                     'created_at': tweet.created_at,
                     'favorite_count': tweet.favorite_count,
                     'retweet_count': tweet.retweet_count,
                     'view_count': getattr(tweet, 'view_count', 0) or 0,
                     'reply_count': getattr(tweet, 'reply_count', 0) or 0,
                     'media': self._extract_media_info(tweet)
                 })
                 
             return results, None
             

        except Exception as e:
             logger.error(f"Error searching tweets: {str(e)}")
             if "429" in str(e):
                 return [], "Rate limit exceeded. Please wait a few minutes."
             return [], f"Error searching tweets: {str(e)}"

    def logout(self):
        """
        Delete cookies file to reset session
        """
        try:
            if os.path.exists(self.cookies_path):
                os.remove(self.cookies_path)
                logger.info("Cookies deleted. Session reset.")
            
            # Clear cache on logout
            self.cache.clear()
            
            return True, "Session reset successfully. Cache cleared."
        except Exception as e:
            logger.error(f"Error resetting session: {str(e)}")
            return False, f"Error resetting session: {str(e)}"
