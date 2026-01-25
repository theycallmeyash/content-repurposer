"""
Twitter Scraper - Advanced Text Extraction Methods
Extends the base TwitterScraper with pattern analysis features
"""

try:
    from data_engine.twitter_scraper import TwitterScraper
except ImportError:
    from .twitter_scraper import TwitterScraper
import asyncio
import httpx
import json
import logging
import re
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import Counter

logger = logging.getLogger(__name__)


class TwitterScraperAdvanced(TwitterScraper):
    """Extended Twitter scraper with advanced text extraction and pattern analysis"""
    
    def __init__(self):
        super().__init__()
        self.bearer_token = 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA'
    
    def _parse_tweet_entities(self, text: str) -> Dict:
        """Parse hashtags, mentions, URLs, and cashtags from tweet text"""
        entities = {
            'hashtags': [],
            'mentions': [],
            'urls': [],
            'cashtags': []
        }
        
        # Extract hashtags
        entities['hashtags'] = re.findall(r'#(\w+)', text)
        
        # Extract mentions
        entities['mentions'] = re.findall(r'@(\w+)', text)
        
        # Extract URLs
        entities['urls'] = re.findall(r'https?://\S+', text)
        
        # Extract cashtags (stock symbols)
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
        # DEBUG: Print raw date to terminal
        print(f"DEBUG: Processing date: '{created_at}'")
        
        dt = None
        try:
            # Try ISO format first (e.g. 2023-01-01T10:00:00Z)
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        except ValueError:
            try:
                # Try legacy Twitter format (e.g. Fri Oct 27 10:00:00 +0000 2023)
                dt = datetime.strptime(created_at, '%a %b %d %H:%M:%S %z %Y')
            except ValueError:
                print(f"DEBUG: Failed to parse date: {created_at}")
                return {
                    'hour_posted': 0,
                    'day_of_week': 'Unknown',
                    'timestamp': created_at
                }
        
        # Valid date found
        # Convert to local time (simulated by just taking hour directly from UTC for now, or adding offset)
        # For simplicity, we stick to the parsed hour
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
            # Set cookies
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
            cached = self.cache.get(cache_key, max_age_seconds=1800)  # 30 min cache
            if cached:
                return cached, None
        
        async def _fetch_tweet():
            # Using Twitter API v1.1 show endpoint
            url = f'https://api.x.com/1.1/statuses/show.json'
            params = {
                'id': tweet_id,
                'tweet_mode': 'extended',
                'include_entities': 'true'
            }
            
            data = await self._make_api_request(url, params)
            
            # Parse the response
            tweet_data = {
                'id': data.get('id_str'),
                'text': data.get('full_text', data.get('text', '')),
                'created_at': data.get('created_at'),
                'language': data.get('lang'),
                'source': re.sub(r'<[^>]+>', '', data.get('source', 'Unknown')),  # Remove HTML tags
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
                    'bookmarks': 0,  # Not available in v1.1
                    'views': 0  # Not available in v1.1
                },
                'conversation': {
                    'is_reply': data.get('in_reply_to_status_id_str') is not None,
                    'reply_to_id': data.get('in_reply_to_status_id_str'),
                    'is_thread': False,  # Would need additional logic
                    'thread_position': 0
                }
            }
            
            # Parse entities
            text = tweet_data['text']
            tweet_data['entities'] = self._parse_tweet_entities(text)
            
            # Calculate metrics
            tweet_data['metrics'] = {
                'text_length': len(text),
                'hashtag_count': len(tweet_data['entities']['hashtags']),
                'mention_count': len(tweet_data['entities']['mentions']),
                'url_count': len(tweet_data['entities']['urls']),
                'has_media': 'media' in data.get('entities', {})
            }
            
            # Timing info
            tweet_data['timing'] = self._extract_timing_info(data.get('created_at', ''))
            
            # Engagement rate (if views available)
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
        # Build search query
        search_query = query
        
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
            cached = self.cache.get(cache_key, max_age_seconds=600)  # 10 min cache
            if cached:
                return cached, None
        
        # Use the base search_tweets method
        tweets, error = self.search_tweets(search_query, product='Top', limit=limit)
        
        if error:
            return [], error
        
        # Enhance with detailed data
        detailed_tweets = []
        for tweet in tweets[:limit]:  # Limit results
            # Add parsed entities
            entities = self._parse_tweet_entities(tweet.get('text', ''))
            
            enhanced_tweet = {
                **tweet,
                'entities': entities,
                'metrics': {
                    'text_length': len(tweet.get('text', '')),
                    'hashtag_count': len(entities['hashtags']),
                    'mention_count': len(entities['mentions']),
                    'url_count': len(entities['urls']),
                },
                'engagement': {
                    'likes': tweet.get('favorite_count', 0),
                    'retweets': tweet.get('retweet_count', 0),
                    'replies': 0,  # Not available in basic search
                    'quotes': 0,
                }
            }
            
            detailed_tweets.append(enhanced_tweet)
        
        if use_cache:
            self.cache.set(cache_key, detailed_tweets)
        
        return detailed_tweets, None
    
    def analyze_hashtag_performance(
        self,
        hashtag: str,
        limit: int = 50
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Analyze hashtag performance and patterns
        Returns statistics about hashtag usage and engagement
        """
        if not hashtag.startswith('#'):
            hashtag = f'#{hashtag}'
        
        # Search for tweets with this hashtag
        tweets, error = self.search_tweets_advanced(
            query=hashtag,
            limit=limit,
            use_cache=True
        )
        
        if error or not tweets:
            return None, error or "No tweets found"
        
        # Analyze patterns
        total_engagement = 0
        total_likes = 0
        total_retweets = 0
        verified_count = 0
        languages = []
        hours = []
        related_hashtags = Counter()
        top_users = Counter()
        
        for tweet in tweets:
            if not isinstance(tweet, dict):
                logger.warning(f"Skipping malformed tweet data: {type(tweet)}")
                continue
            engagement = tweet.get('engagement', {})
            total_likes += engagement.get('likes', 0)
            total_retweets += engagement.get('retweets', 0)
            total_engagement += total_likes + total_retweets
            
            # Count verified users
            if tweet.get('user', {}).get('verified'):
                verified_count += 1
            
            # Track languages
            if 'language' in tweet:
                languages.append(tweet['language'])
            
            # Track posting hours
            if 'timing' in tweet:
                hours.append(tweet['timing'].get('hour_posted', 0))
            
            # Related hashtags
            for tag in tweet.get('entities', {}).get('hashtags', []):
                if tag.lower() != hashtag.lower().replace('#', ''):
                    related_hashtags[tag] += 1
            
            # Top users
            screen_name = tweet.get('screen_name', tweet.get('user', {}).get('screen_name'))
            if screen_name:
                top_users[screen_name] += 1
        
        analysis = {
            'hashtag': hashtag,
            'tweet_count': len(tweets),
            'total_engagement': total_engagement,
            'avg_likes': round(total_likes / len(tweets), 2) if tweets else 0,
            'avg_retweets': round(total_retweets / len(tweets), 2) if tweets else 0,
            'verified_percentage': round((verified_count / len(tweets)) * 100, 2) if tweets else 0,
            'top_related_hashtags': [{'hashtag': f'#{tag}', 'count': count} 
                                     for tag, count in related_hashtags.most_common(10)],
            'top_contributors': [{'user': user, 'tweet_count': count} 
                                for user, count in top_users.most_common(10)],
            'language_distribution': dict(Counter(languages).most_common(5)),
            'peak_hours': dict(Counter(hours).most_common(5))
        }
        
        return analysis, None
    
    def find_viral_content(
        self,
        query: str = "",
        min_engagement: int = 1000,
        hours: int = 24,
        limit: int = 20
    ) -> Tuple[List[Dict], Optional[str]]:
        """
        Find viral content based on engagement thresholds
        """
        # Build query for recent viral content
        search_query = query if query else "filter:follows"  # Popular tweets
        
        # Search with high engagement filter
        tweets, error = self.search_tweets_advanced(
            query=search_query,
            limit=limit * 2,  # Get more to filter
            min_likes=min_engagement // 2,  # Use half for initial filter
            use_cache=True
        )
        
        if error:
            return [], error
        
        # Filter by total engagement
        viral_tweets = []
        for tweet in tweets:
            engagement = tweet.get('engagement', {})
            total = engagement.get('likes', 0) + engagement.get('retweets', 0)
            
            if total >= min_engagement:
                tweet['total_engagement'] = total
                viral_tweets.append(tweet)
        
        # Sort by engagement
        viral_tweets.sort(key=lambda x: x.get('total_engagement', 0), reverse=True)
        
        return viral_tweets[:limit], None
    
    def get_user_timeline(
        self,
        username: str,
        limit: int = 50,
        include_replies: bool = False,
        include_retweets: bool = False
    ) -> Tuple[List[Dict], Optional[str]]:
        """
        Get user's recent tweets with text analysis
        """
        # Build search query for user timeline
        query = f"from:{username}"
        
        if not include_replies:
            query += " -filter:replies"
        if not include_retweets:
            query += " -filter:retweets"
        
        tweets, error = self.search_tweets_advanced(
            query=query,
            limit=limit,
            use_cache=True
        )
        
        return tweets, error
    
    def analyze_user_patterns(
        self,
        username: str,
        tweet_limit: int = 100
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Analyze a user's tweeting patterns and performance
        """
        tweets, error = self.get_user_timeline(username, limit=tweet_limit)
        
        if error or not tweets:
            return None, error or "No tweets found"
        
        # Analyze patterns
        total_likes = 0
        total_retweets = 0
        all_hashtags = Counter()
        all_mentions = Counter()
        hours = []
        days = []
        text_lengths = []
        
        for tweet in tweets:
            engagement = tweet.get('engagement', {})
            total_likes += engagement.get('likes', 0)
            total_retweets += engagement.get('retweets', 0)
            
            # Collect hashtags
            for tag in tweet.get('entities', {}).get('hashtags', []):
                all_hashtags[tag] += 1
            
            # Collect mentions
            for mention in tweet.get('entities', {}).get('mentions', []):
                all_mentions[mention] += 1
            
            # Timing
            if 'timing' in tweet:
                hours.append(tweet['timing'].get('hour_posted', 0))
                days.append(tweet['timing'].get('day_of_week', 'Unknown'))
            
            # Text length
            text_lengths.append(tweet.get('metrics', {}).get('text_length', 0))
        
        analysis = {
            'username': username,
            'tweet_count': len(tweets),
            'avg_likes': round(total_likes / len(tweets), 2) if tweets else 0,
            'avg_retweets': round(total_retweets / len(tweets), 2) if tweets else 0,
            'total_engagement': total_likes + total_retweets,
            'most_used_hashtags': [{'hashtag': f'#{tag}', 'count': count} 
                                   for tag, count in all_hashtags.most_common(10)],
            'most_mentioned': [{'user': f'@{user}', 'count': count} 
                              for user, count in all_mentions.most_common(10)],
            'peak_posting_hours': dict(Counter(hours).most_common(5)),
            'posting_days': dict(Counter(days).most_common()),
            'avg_text_length': round(sum(text_lengths) / len(text_lengths), 2) if text_lengths else 0,
            'optimal_length_range': f"{min(text_lengths)}-{max(text_lengths)}" if text_lengths else "0-0"
        }
        
        return analysis, None

        return analysis, None

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 Initializing Advanced Scraper...")
    scraper = TwitterScraperAdvanced()
    
    # Simple test
    print("\n🔎 Searching for viral 'AI' tweets...")
    tweets, error = scraper.find_viral_content("AI", min_engagement=100, limit=5)
    
    if error:
        print(f"Error: {error}")
    else:
        for i, t in enumerate(tweets, 1):
            print(f"\n{i}. {t['text'][:80]}...")
            print(f"   ❤️ {t.get('total_engagement')} | @{t['screen_name']}")
# For backward compatibility, export both classes
__all__ = ['TwitterScraper', 'TwitterScraperAdvanced']
