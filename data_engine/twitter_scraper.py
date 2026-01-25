from twikit import Client
import json
import os
import logging
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

from twikit import Client
import json
import os
import logging
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

class TwitterScraper:
    def __init__(self):
        self.cookies_path = 'twitter_cookies.json'
        
    def _get_client(self):
        """Get a fresh client instance"""
        client = Client('en-US', http2=True)
        return client

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
                # Verify cookies work by doing a quick valid check if possible, 
                # but for now assume they are good to avoid extra calls.
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
            return True, "Cookies imported and converted successfully! Try fetching trends now."
            
        except json.JSONDecodeError:
            return False, "Invalid JSON format. Please paste a valid JSON object."
        except Exception as e:
            logger.error(f"Manual cookie import failed: {str(e)}")
            return False, f"Import failed: {str(e)}"

    def get_trends(self):
        """
        Fetch current trends
        """
        async def _trends_task():
            import httpx
            try:
                # Use a fresh, standalone httpx client with HTTP/2 enabled
                # This bypasses any twikit wrappers that might be downgrading to HTTP/1.1
                async with httpx.AsyncClient(http2=True) as http_client:
                    logger.info("DEBUG: Created standalone httpx client (HTTP/2)")
                    
                    # Reload cookies
                    import json
                    with open(self.cookies_path, 'r') as f:
                        saved_cookies = json.load(f)
                    
                    # Set cookies for .x.com
                    for name, value in saved_cookies.items():
                        http_client.cookies.set(name, value, domain='.x.com')

                    csrf_token = saved_cookies.get('ct0')
                    if not csrf_token:
                        logger.warning("DEBUG: 'ct0' cookie not found!")

                    headers = {
                        'x-csrf-token': csrf_token,
                        'x-twitter-active-user': 'yes',
                        'x-twitter-auth-type': 'OAuth2Session',
                        'x-twitter-client-language': 'en',
                        'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
                        'Referer': 'https://x.com/',
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    }
                    
                    url = 'https://api.x.com/1.1/trends/place.json'
                    params = {'id': '1'} 

                    logger.info(f"DEBUG: Making manual request to {url} [STANDALONE HTTP/2]")
                    response = await http_client.get(url, params=params, headers=headers)
                    
                    if response.status_code != 200:
                        logger.error(f"DEBUG: API returned {response.status_code}: {response.text[:200]}")
                        raise Exception(f"API Error {response.status_code}")
                        
                    data = response.json()
                    
                    # Manual Parsing
                    trends = []
                    if isinstance(data, list) and len(data) > 0:
                        trends = data[0].get('trends', [])
                    
                    logger.info(f"DEBUG: Manually extracted {len(trends)} trends")
                    return trends
                
            except Exception as e:
                import traceback
                logger.error(f"DEBUG: Async Task Crash: {traceback.format_exc()}")
                raise e

        try:
            if not os.path.exists(self.cookies_path):
                 return [], "Not logged in. Please login first."

            trends = asyncio.run(_trends_task())
            
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
                    'domain': 'Trending', # Place API doesn't give domain context
                })

            return formatted_trends, None
            
        except Exception as e:
            logger.error(f"Error fetching trends: {str(e)}")
            if "too many values to unpack" in str(e):
                 return [], "API Error: Unexpected data format from X. Please retry."
            if "403" in str(e):
                 return [], "Error 403: Access Denied. Your account might be locked or the cookies are invalid. Try deleting 'twitter_cookies.json' and logging in again."
            return [], f"Error fetching trends: {str(e)}"
    
    def search_tweets(self, query, product='Top', limit=20):
        """
        Search for tweets
        product: 'Top', 'Latest', 'Media'
        """
        async def _search_task():
            client = self._get_client()
            client.load_cookies(self.cookies_path)
            return await client.search_tweet(query, product=product, count=limit)

        try:
             if not os.path.exists(self.cookies_path):
                 return [], "Not logged in. Please login first."
             
             tweets = asyncio.run(_search_task())
             
             results = []
             for tweet in tweets:
                 results.append({
                     'id': tweet.id,
                     'text': tweet.text,
                     'user': tweet.user.name,
                     'screen_name': tweet.user.screen_name,
                     'created_at': tweet.created_at,
                     'favorite_count': tweet.favorite_count,
                     'retweet_count': tweet.retweet_count
                 })
                 
             return tweets, None
             

        except Exception as e:
             logger.error(f"Error searching tweets: {str(e)}")
             if "Event loop" in str(e):
                 return [], "System Error: Event loop closed. Please retry."
             return [], f"Error searching tweets: {str(e)}"

    def logout(self):
        """
        Delete cookies file to reset session
        """
        try:
            if os.path.exists(self.cookies_path):
                os.remove(self.cookies_path)
                logger.info("Cookies deleted. Session reset.")
                return True, "Session reset successfully. Please log in again."
            return True, "No session found to reset."
        except Exception as e:
            logger.error(f"Error resetting session: {str(e)}")
            return False, f"Error resetting session: {str(e)}"
