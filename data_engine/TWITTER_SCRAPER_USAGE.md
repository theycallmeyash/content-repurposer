# Twitter Scraper Enhancement - Usage Examples

## Basic Usage

### 1. Initialize the Scraper

```python
from data_engine.twitter_scraper_advanced import TwitterScraperAdvanced

scraper = TwitterScraperAdvanced()
```

### 2. Fetch Trends (with caching)

```python
# Fetch Global trends (default WOEID=1)
trends, error = scraper.get_trends(use_cache=True)

# Fetch trends for specific location (e.g., US = 23424977, India = 23424848)
trends_us, error = scraper.get_trends(woeid=23424977)

if not error:
    for trend in trends[:10]:
        print(f"{trend['keyword']}: {trend['volume']} tweets")
```

### 3. Get Detailed Tweet Information

```python
# Fetch complete tweet data with parsed entities
tweet_data, error = scraper.get_tweet_details(tweet_id="1234567890")

if not error:
    print(f"Text: {tweet_data['text']}")
    print(f"Likes: {tweet_data['engagement']['likes']}")
    print(f"Hashtags: {tweet_data['entities']['hashtags']}")
    print(f"Posted at: {tweet_data['timing']['hour_posted']}:00")
```

### 4. Advanced Search with Filters

```python
# Search with engagement filters
tweets, error = scraper.search_tweets_advanced(
    query="artificial intelligence",
    limit=50,
    min_likes=100,
    min_retweets=20,
    verified_only=True,
    language="en"
)

for tweet in tweets:
    print(f"@{tweet['screen_name']}: {tweet['text'][:100]}...")
```

### 5. Analyze Hashtag Performance

```python
# Get insights about a hashtag
analysis, error = scraper.analyze_hashtag_performance("#AI", limit=100)

if not error:
    print(f"Total tweets: {analysis['tweet_count']}")
    print(f"Avg engagement: {analysis['avg_likes']} likes")
    print(f"Top related: {analysis['top_related_hashtags']}")
    print(f"Peak hours: {analysis['peak_hours']}")
```

### 6. Find Viral Content

```python
# Detect viral tweets
viral_tweets, error = scraper.find_viral_content(
    query="technology",
    min_engagement=10000,
    limit=20
)

for tweet in viral_tweets:
    print(f"Viral: {tweet['total_engagement']:,} engagement")
    print(f"Text: {tweet['text']}")
```

### 7. Analyze User Patterns

```python
# Understand what works for a user
analysis, error = scraper.analyze_user_patterns("username", tweet_limit=100)

if not error:
    print(f"Avg likes: {analysis['avg_likes']}")
    print(f"Best hashtags: {analysis['most_used_hashtags']}")
    print(f"Peak posting time: {analysis['peak_posting_hours']}")
    print(f"Optimal text length: {analysis['avg_text_length']}")
```

### 8. Get User Timeline

```python
# Fetch user's recent tweets
tweets, error = scraper.get_user_timeline(
    username="elonmusk",
    limit=50,
    include_replies=False,
    include_retweets=False
)

for tweet in tweets:
    print(f"{tweet['created_at']}: {tweet['text']}")
```

## Pattern Analysis for Algorithm Insights

### Understanding What Works on X

```python
# 1. Analyze top performing content in your niche
viral_tweets, _ = scraper.find_viral_content(
    query="your_niche_keyword",
    min_engagement=5000,
    limit=50
)

# Extract patterns
hashtag_usage = []
text_lengths = []
posting_times = []

for tweet in viral_tweets:
    hashtag_usage.append(len(tweet['entities']['hashtags']))
    text_lengths.append(tweet['metrics']['text_length'])
    posting_times.append(tweet['timing']['hour_posted'])

print(f"Avg hashtags in viral tweets: {sum(hashtag_usage)/len(hashtag_usage)}")
print(f"Avg text length: {sum(text_lengths)/len(text_lengths)}")
print(f"Most common posting hour: {max(set(posting_times), key=posting_times.count)}")
```

### Compare Your Performance vs Competitors

```python
# Analyze your account
your_analysis, _ = scraper.analyze_user_patterns("your_username", 100)

# Analyze competitor
competitor_analysis, _ = scraper.analyze_user_patterns("competitor", 100)

print(f"Your avg engagement: {your_analysis['avg_likes'] + your_analysis['avg_retweets']}")
print(f"Competitor avg: {competitor_analysis['avg_likes'] + competitor_analysis['avg_retweets']}")

print(f"\nYour best hashtags: {your_analysis['most_used_hashtags'][:5]}")
print(f"Their best hashtags: {competitor_analysis['most_used_hashtags'][:5]}")
```

### Track Hashtag Trends Over Time

```python
import time

# Track a hashtag's performance
hashtag = "#AI"

for i in range(3):  # Check 3 times over 30 minutes
    analysis, _ = scraper.analyze_hashtag_performance(hashtag, limit=50)
    
    print(f"\nCheck {i+1}:")
    print(f"  Tweet volume: {analysis['tweet_count']}")
    print(f"  Avg engagement: {analysis['avg_likes']}")
    
    if i < 2:
        time.sleep(600)  # Wait 10 minutes
```

## Integration with Content Repurposer

### Example: Find Trending Topics for Content Ideas

```python
# Get current trends
trends, _ = scraper.get_trends()

# Analyze each trend for content opportunities
for trend in trends[:5]:
    keyword = trend['keyword']
    
    # Get top tweets for this trend
    tweets, _ = scraper.search_tweets_advanced(
        query=keyword,
        limit=20,
        min_likes=500
    )
    
    # Analyze what's working
    if tweets:
        avg_hashtags = sum(len(t['entities']['hashtags']) for t in tweets) / len(tweets)
        avg_length = sum(t['metrics']['text_length'] for t in tweets) / len(tweets)
        
        print(f"\nTrend: {keyword}")
        print(f"  Content strategy:")
        print(f"    - Use ~{int(avg_hashtags)} hashtags")
        print(f"    - Keep text around {int(avg_length)} characters")
        print(f"    - Related tags: {tweets[0]['entities']['hashtags'][:3]}")
```

## Rate Limiting & Caching

The scraper automatically handles:
- **Rate limiting**: Max 50 requests per 15 minutes
- **Retry logic**: 3 retries with exponential backoff
- **Caching**: 
  - Trends: 10 minutes
  - Tweet details: 30 minutes
  - Search results: 10 minutes

```python
# Force fresh data (bypass cache)
trends, _ = scraper.get_trends(use_cache=False)

# Use longer cache TTL
trends, _ = scraper.get_trends(use_cache=True, cache_ttl=1800)  # 30 min
```

## Error Handling

```python
data, error = scraper.get_tweet_details("123456")

if error:
    if "403" in error:
        print("Access denied - cookies may be invalid")
    elif "429" in error:
        print("Rate limited - wait a few minutes")
    elif "404" in error:
        print("Tweet not found")
    else:
        print(f"Error: {error}")
else:
    # Process data
    print(data)
```
