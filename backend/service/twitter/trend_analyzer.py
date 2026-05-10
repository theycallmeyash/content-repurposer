import logging
from typing import Dict, List, Optional, Tuple
from collections import Counter

logger = logging.getLogger(__name__)

class TwitterTrendAnalyzer:
    """Service class focused on broad dataset patterns like hashtags and viruses."""
    
    def __init__(self, scraper=None):
        if scraper is None:
            from .scraper import TwitterScraperAdvanced
            self.scraper = TwitterScraperAdvanced()
        else:
            self.scraper = scraper

    def analyze_hashtag_performance(
        self,
        hashtag: str,
        limit: int = 50
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """Analyze hashtag performance and patterns"""
        if not hashtag.startswith('#'):
            hashtag = f'#{hashtag}'
            
        tweets, error = self.scraper.search_tweets_advanced(
            query=hashtag,
            limit=limit,
            use_cache=True
        )
        
        if error or not tweets:
            return None, error or "No tweets found"
            
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
            
            if tweet.get('user', {}).get('verified'):
                verified_count += 1
                
            if 'language' in tweet:
                languages.append(tweet['language'])
                
            if 'timing' in tweet:
                hours.append(tweet['timing'].get('hour_posted', 0))
                
            for tag in tweet.get('entities', {}).get('hashtags', []):
                if tag.lower() != hashtag.lower().replace('#', ''):
                    related_hashtags[tag] += 1
                    
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
            'top_related_hashtags': [{'hashtag': f'#{tag}', 'count': count} for tag, count in related_hashtags.most_common(10)],
            'top_contributors': [{'user': user, 'tweet_count': count} for user, count in top_users.most_common(10)],
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
        """Find viral content based on engagement thresholds"""
        search_query = query if query else "filter:follows"
        
        tweets, error = self.scraper.search_tweets_advanced(
            query=search_query,
            limit=limit * 2,
            min_likes=min_engagement // 2,
            use_cache=True
        )
        
        if error:
            return [], error
            
        viral_tweets = []
        for tweet in tweets:
            engagement = tweet.get('engagement', {})
            total = engagement.get('likes', 0) + engagement.get('retweets', 0)
            
            if total >= min_engagement:
                tweet['total_engagement'] = total
                viral_tweets.append(tweet)
                
        viral_tweets.sort(key=lambda x: x.get('total_engagement', 0), reverse=True)
        return viral_tweets[:limit], None
