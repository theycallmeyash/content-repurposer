import asyncio
import httpx
import json
import logging
import re
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from data_engine.twitter_scraper import TwitterScraper

logger = logging.getLogger(__name__)

class TwitterScraperAdvanced(TwitterScraper):
    """Extended Twitter scraper with advanced text extraction and API fetching logic."""
    
    def __init__(self):
        super().__init__()
        self.bearer_token = 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA'
    
    @staticmethod
    def _safe_int(val, default=0):
        """Safely convert a value to int, handling strings and None."""
        if val is None:
            return default
        try:
            return int(val)
        except (ValueError, TypeError):
            return default
    
    def _parse_tweet_entities(self, text: str) -> Dict:
        """Parse hashtags, mentions, URLs, and cashtags from tweet text"""
        entities = {
            'hashtags': [],
            'mentions': [],
            'urls': [],
            'cashtags': []
        }
        
        entities['hashtags'] = re.findall(r'#(\w+)', text)
        entities['mentions'] = re.findall(r'@(\w+)', text)
        entities['urls'] = re.findall(r'https?://\S+', text)
        entities['cashtags'] = re.findall(r'\$([A-Z]{1,5})', text)
        
        return entities
    
    def _calculate_engagement_rate(self, engagement: Dict, views: int) -> float:
        """Calculate engagement rate"""
        if views == 0:
            return 0.0
        
        total_engagement = (
            engagement.get('likes', 0) +
            engagement.get('retweets', 0) +
            engagement.get('replies', 0) +
            engagement.get('quotes', 0)
        )
        
        return round((total_engagement / views) * 100, 2)
    
    def _extract_timing_info(self, created_at: str) -> Dict:
        """Extract timing information from tweet"""
        print(f"DEBUG: Processing date: '{created_at}'")
        
        dt = None
        try:
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        except ValueError:
            try:
                dt = datetime.strptime(created_at, '%a %b %d %H:%M:%S %z %Y')
            except ValueError:
                print(f"DEBUG: Failed to parse date: {created_at}")
                return {
                    'hour_posted': 0,
                    'day_of_week': 'Unknown',
                    'timestamp': created_at
                }
        
        print(f"DEBUG: Extracted Hour: {dt.hour}")
        return {
            'hour_posted': dt.hour,
            'day_of_week': dt.strftime('%A'),
            'timestamp': dt.isoformat()
        }
    
    async def _make_api_request(self, url: str, params: Dict = None) -> Dict:
        """Make authenticated API request to X"""
        self._check_rate_limit()
        
        with open(self.cookies_path, 'r') as f:
            saved_cookies = json.load(f)
        
        async with httpx.AsyncClient(http2=True, timeout=30.0) as http_client:
            for name, value in saved_cookies.items():
                http_client.cookies.set(name, value, domain='.x.com')
            
            csrf_token = saved_cookies.get('ct0', '')
            
            headers = {
                'x-csrf-token': csrf_token,
                'x-twitter-active-user': 'yes',
                'x-twitter-auth-type': 'OAuth2Session',
                'x-twitter-client-language': 'en',
                'authorization': self.bearer_token,
                'Referer': 'https://x.com/',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = await http_client.get(url, params=params, headers=headers)
            
            if response.status_code == 429:
                raise Exception("Rate limit exceeded")
            elif response.status_code != 200:
                raise Exception(f"API Error {response.status_code}: {response.text[:200]}")
            
            return response.json()
    
    def get_tweet_details(self, tweet_id: str, use_cache=True) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Fetch detailed tweet information (text-focused)
        Returns comprehensive tweet data with engagement metrics and parsed entities
        """
        cache_key = f"tweet_{tweet_id}"
        
        if use_cache:
            cached = self.cache.get(cache_key, max_age_seconds=1800)
            if cached:
                return cached, None
        
        async def _fetch_tweet():
            url = f'https://api.x.com/1.1/statuses/show.json'
            params = {
                'id': tweet_id,
                'tweet_mode': 'extended',
                'include_entities': 'true'
            }
            
            data = await self._make_api_request(url, params)
            
            tweet_data = {
                'id': data.get('id_str'),
                'text': data.get('full_text', data.get('text', '')),
                'created_at': data.get('created_at'),
                'language': data.get('lang'),
                'source': re.sub(r'<[^>]+>', '', data.get('source', 'Unknown')),
                'user': {
                    'id': data.get('user', {}).get('id_str'),
                    'name': data.get('user', {}).get('name'),
                    'screen_name': data.get('user', {}).get('screen_name'),
                    'verified': data.get('user', {}).get('verified', False),
                    'followers_count': data.get('user', {}).get('followers_count', 0),
                    'following_count': data.get('user', {}).get('friends_count', 0),
                    'tweet_count': data.get('user', {}).get('statuses_count', 0)
                },
                'engagement': {
                    'likes': data.get('favorite_count', 0),
                    'retweets': data.get('retweet_count', 0),
                    'replies': data.get('reply_count', 0),
                    'quotes': data.get('quote_count', 0),
                    'bookmarks': 0,
                    'views': 0
                },
                'conversation': {
                    'is_reply': data.get('in_reply_to_status_id_str') is not None,
                    'reply_to_id': data.get('in_reply_to_status_id_str'),
                    'is_thread': False,
                    'thread_position': 0
                }
            }
            
            text = tweet_data['text']
            tweet_data['entities'] = self._parse_tweet_entities(text)
            
            tweet_data['metrics'] = {
                'text_length': len(text),
                'hashtag_count': len(tweet_data['entities']['hashtags']),
                'mention_count': len(tweet_data['entities']['mentions']),
                'url_count': len(tweet_data['entities']['urls']),
                'has_media': 'media' in data.get('entities', {})
            }
            
            tweet_data['timing'] = self._extract_timing_info(data.get('created_at', ''))
            
            views = tweet_data['engagement']['views']
            if views > 0:
                tweet_data['engagement']['engagement_rate'] = self._calculate_engagement_rate(
                    tweet_data['engagement'], views
                )
            else:
                tweet_data['engagement']['engagement_rate'] = 0.0
            
            return tweet_data
        
        try:
            def fetch():
                return asyncio.run(_fetch_tweet())
            
            tweet_data = self._retry_with_backoff(fetch)
            
            if use_cache:
                self.cache.set(cache_key, tweet_data)
            
            return tweet_data, None
            
        except Exception as e:
            logger.error(f"Error fetching tweet {tweet_id}: {str(e)}")
            return None, f"Error: {str(e)}"
    
    def search_tweets_advanced(
        self,
        query: str,
        limit: int = 20,
        min_likes: int = 0,
        min_retweets: int = 0,
        verified_only: bool = False,
        language: str = None,
        use_cache: bool = True
    ) -> Tuple[List[Dict], Optional[str]]:
        """
        Advanced tweet search with filters
        Returns list of detailed tweet objects
        """
        search_query = query
        print(f"Search query -- : {search_query}")
        if min_likes > 0:
            search_query += f" min_faves:{min_likes}"
        if min_retweets > 0:
            search_query += f" min_retweets:{min_retweets}"
        if verified_only:
            search_query += " filter:verified"
        if language:
            search_query += f" lang:{language}"
        
        cache_key = f"search_{hashlib.md5(search_query.encode()).hexdigest()}_{limit}"
        
        if use_cache:
            cached = self.cache.get(cache_key, max_age_seconds=600)
            if cached:
                return cached, None
        
        tweets, error = self.search_tweets(search_query, product='Top', limit=limit)
        
        if error:
            return [], error
        
        detailed_tweets = []
        for tweet in tweets[:limit]:
            entities = self._parse_tweet_entities(tweet.get('text', ''))
            
            media = tweet.get('media', {})
            has_urls = len(entities['urls']) > 0
            has_media = media.get('has_media', False)
            if has_media:
                content_type = 'media'
            elif has_urls:
                content_type = 'link'
            else:
                content_type = 'text_only'
            
            enhanced_tweet = {
                **tweet,
                'entities': entities,
                'content_type': content_type,
                'metrics': {
                    'text_length': len(tweet.get('text', '')),
                    'hashtag_count': len(entities['hashtags']),
                    'mention_count': len(entities['mentions']),
                    'url_count': len(entities['urls']),
                    'has_media': has_media,
                    'media_type': media.get('type'),
                },
                'engagement': {
                    'likes': self._safe_int(tweet.get('favorite_count', 0)),
                    'retweets': self._safe_int(tweet.get('retweet_count', 0)),
                    'replies': self._safe_int(tweet.get('reply_count', 0)),
                    'views': self._safe_int(tweet.get('view_count', 0)),
                    'quotes': 0,
                }
            }
            
            detailed_tweets.append(enhanced_tweet)
        
        if use_cache:
            self.cache.set(cache_key, detailed_tweets)
        
        return detailed_tweets, None
