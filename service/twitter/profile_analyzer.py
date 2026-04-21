import logging
from typing import Dict, List, Optional, Tuple
from collections import Counter

logger = logging.getLogger(__name__)

class TwitterProfileAnalyzer:
    """Service class focused on individual user patterns and profiles."""
    
    def __init__(self, scraper=None):
        if scraper is None:
            from .scraper import TwitterScraperAdvanced
            self.scraper = TwitterScraperAdvanced()
        else:
            self.scraper = scraper
    print('inside profile analyzer')
    def get_user_timeline(
        self,
        username: str,
        limit: int = 50,
        include_replies: bool = False,
        include_retweets: bool = False
    ) -> Tuple[List[Dict], Optional[str]]:
        """Get user's recent tweets with text analysis"""
        query = f"from:{username}"
        if not include_replies:
            query += " -filter:replies"
        if not include_retweets:
            query += " -filter:retweets"
        
        return self.scraper.search_tweets_advanced(
            query=query,
            limit=limit,
            use_cache=True
        )

    def analyze_user_patterns(
        self,
        username: str,
        tweet_limit: int = 100
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Analyze a user's tweeting patterns and performance.
        Returns comprehensive analysis including content type breakdown and viral insights.
        """
        tweets, error = self.get_user_timeline(username, limit=tweet_limit)
        
        if error or not tweets:
            print(f"Error: {error}")
            return None, error or "No tweets found"
            
        total_likes = 0
        total_retweets = 0
        total_views = 0
        all_hashtags = Counter()
        all_mentions = Counter()
        hours = []
        days = []
        text_lengths = []
        
        content_types = {'text_only': [], 'media': [], 'link': []}
        
        for tweet in tweets:
            engagement = tweet.get('engagement', {})
            likes = self.scraper._safe_int(engagement.get('likes', 0))
            retweets = self.scraper._safe_int(engagement.get('retweets', 0))
            views = self.scraper._safe_int(engagement.get('views', 0))
            
            total_likes += likes
            total_retweets += retweets
            total_views += views
            
            ct = tweet.get('content_type', 'text_only')
            total_eng = likes + retweets
            
            if ct not in content_types:
                content_types[ct] = []
                
            content_types[ct].append({
                'likes': likes,
                'retweets': retweets,
                'views': views,
                'total': total_eng,
                'text': tweet.get('text', ''),
                'media_type': tweet.get('metrics', {}).get('media_type'),
                'text_length': tweet.get('metrics', {}).get('text_length', 0),
            })
            
            for tag in tweet.get('entities', {}).get('hashtags', []):
                all_hashtags[tag] += 1
            for mention in tweet.get('entities', {}).get('mentions', []):
                all_mentions[mention] += 1
            
            if 'timing' in tweet:
                hours.append(tweet['timing'].get('hour_posted', 0))
                days.append(tweet['timing'].get('day_of_week', 'Unknown'))
            
            text_lengths.append(tweet.get('metrics', {}).get('text_length', 0))
            
        content_type_breakdown = {}
        for ct, items in content_types.items():
            if items:
                ct_likes = [i['likes'] for i in items]
                ct_retweets = [i['retweets'] for i in items]
                content_type_breakdown[ct] = {
                    'count': len(items),
                    'avg_likes': round(sum(ct_likes) / len(ct_likes), 1),
                    'avg_retweets': round(sum(ct_retweets) / len(ct_retweets), 1),
                    'total_engagement': sum(i['total'] for i in items),
                }
            else:
                content_type_breakdown[ct] = {'count': 0, 'avg_likes': 0, 'avg_retweets': 0, 'total_engagement': 0}
                
        all_tweet_data = []
        for tweet in tweets:
            eng = tweet.get('engagement', {})
            t_likes = self.scraper._safe_int(eng.get('likes', 0))
            t_retweets = self.scraper._safe_int(eng.get('retweets', 0))
            t_views = self.scraper._safe_int(eng.get('views', 0))
            total_eng = t_likes + t_retweets
            all_tweet_data.append({
                'text': tweet.get('text', ''),
                'likes': t_likes,
                'retweets': t_retweets,
                'views': t_views,
                'total_engagement': total_eng,
                'content_type': tweet.get('content_type', 'text_only'),
                'created_at': tweet.get('created_at', ''),
                'id': tweet.get('id', ''),
                'screen_name': tweet.get('screen_name', username),
            })
            
        all_tweet_data.sort(key=lambda x: x['total_engagement'], reverse=True)
        top_tweets = all_tweet_data[:10]
        bottom_tweets = all_tweet_data[-5:]  # Support for PRISMAI LLM prompt
        bottom_tweets.reverse()
        
        # Calculate max safely
        if content_type_breakdown and sum(v['count'] for v in content_type_breakdown.values()) > 0:
            best_ct = max(content_type_breakdown, key=lambda k: content_type_breakdown[k]['avg_likes'])
        else:
            best_ct = 'text_only'
            
        hour_counts = Counter(hours)
        day_counts = Counter(days)
        best_hour = hour_counts.most_common(1)[0][0] if hour_counts else 0
        best_day = day_counts.most_common(1)[0][0] if day_counts else 'Unknown'
        
        top_lengths = [len(t['text']) for t in top_tweets[:5]] if top_tweets else [0]
        
        viral_insights = {
            'best_content_type': best_ct,
            'best_posting_hour': best_hour,
            'best_posting_day': best_day,
            'avg_viral_length': round(sum(top_lengths) / len(top_lengths)) if top_lengths else 0,
        }
        
        analysis = {
            'username': username,
            'tweet_count': len(tweets),
            'avg_likes': round(total_likes / len(tweets), 2) if tweets else 0,
            'avg_retweets': round(total_retweets / len(tweets), 2) if tweets else 0,
            'total_engagement': total_likes + total_retweets,
            'total_views': total_views,
            'most_used_hashtags': [{'hashtag': f'#{tag}', 'count': count} for tag, count in all_hashtags.most_common(10)],
            'most_mentioned': [{'user': f'@{user}', 'count': count} for user, count in all_mentions.most_common(10)],
            'peak_posting_hours': dict(Counter(hours).most_common(5)),
            'posting_days': dict(Counter(days).most_common()),
            'avg_text_length': round(sum(text_lengths) / len(text_lengths), 2) if text_lengths else 0,
            'optimal_length_range': f"{min(text_lengths)}-{max(text_lengths)}" if text_lengths else "0-0",
            'content_type_breakdown': content_type_breakdown,
            'top_tweets': top_tweets,
            'bottom_tweets': bottom_tweets,
            'viral_insights': viral_insights,
        }
        
        return analysis, None
