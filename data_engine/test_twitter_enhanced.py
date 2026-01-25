"""
Test script for enhanced Twitter scraper
Run this to verify the new features work correctly
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from twitter_scraper_advanced import TwitterScraperAdvanced
import json


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")


def test_trends():
    """Test trend fetching with caching"""
    print_section("Testing Trend Fetching (with cache)")
    
    scraper = TwitterScraperAdvanced()
    
    # First fetch (from API)
    print("Fetching trends (should hit API)...")
    trends, error = scraper.get_trends(use_cache=True)
    
    if error:
        print(f"❌ Error: {error}")
        return False
    
    print(f"✅ Fetched {len(trends)} trends")
    for i, trend in enumerate(trends[:5], 1):
        print(f"  {i}. {trend['keyword']} - {trend['volume']} tweets")
    
    # Second fetch (from cache)
    print("\nFetching trends again (should use cache)...")
    trends2, error2 = scraper.get_trends(use_cache=True)
    
    if error2:
        print(f"❌ Error: {error2}")
        return False
    
    print(f"✅ Fetched {len(trends2)} trends from cache")
    return True


def test_search_advanced():
    """Test advanced search with filters"""
    print_section("Testing Advanced Search")
    
    scraper = TwitterScraperAdvanced()
    
    query = "AI"
    print(f"Searching for: '{query}' (min 100 likes, top 10 results)")
    
    tweets, error = scraper.search_tweets_advanced(
        query=query,
        limit=10,
        min_likes=100,
        use_cache=True
    )
    
    if error:
        print(f"❌ Error: {error}")
        return False
    
    print(f"✅ Found {len(tweets)} tweets")
    
    for i, tweet in enumerate(tweets[:3], 1):
        print(f"\n  Tweet {i}:")
        print(f"    User: @{tweet.get('screen_name', 'unknown')}")
        print(f"    Text: {tweet.get('text', '')[:100]}...")
        print(f"    Likes: {tweet.get('engagement', {}).get('likes', 0)}")
        print(f"    Hashtags: {', '.join(tweet.get('entities', {}).get('hashtags', []))}")
    
    return True


def test_hashtag_analysis():
    """Test hashtag performance analysis"""
    print_section("Testing Hashtag Analysis")
    
    scraper = TwitterScraperAdvanced()
    
    hashtag = "#AI"
    print(f"Analyzing hashtag: {hashtag}")
    
    analysis, error = scraper.analyze_hashtag_performance(hashtag, limit=30)
    
    if error:
        print(f"❌ Error: {error}")
        return False
    
    print(f"✅ Analysis complete!")
    print(f"\n  Tweet Count: {analysis['tweet_count']}")
    print(f"  Total Engagement: {analysis['total_engagement']:,}")
    print(f"  Avg Likes: {analysis['avg_likes']}")
    print(f"  Avg Retweets: {analysis['avg_retweets']}")
    print(f"  Verified Users: {analysis['verified_percentage']}%")
    
    print(f"\n  Top Related Hashtags:")
    for tag in analysis['top_related_hashtags'][:5]:
        print(f"    {tag['hashtag']} ({tag['count']} times)")
    
    print(f"\n  Peak Posting Hours:")
    for hour, count in list(analysis['peak_hours'].items())[:3]:
        print(f"    {hour}:00 - {count} tweets")
    
    return True


def test_viral_content():
    """Test viral content detection"""
    print_section("Testing Viral Content Detection")
    
    scraper = TwitterScraperAdvanced()
    
    print("Finding viral tweets (min 5000 engagement)...")
    
    viral_tweets, error = scraper.find_viral_content(
        query="",
        min_engagement=5000,
        limit=5
    )
    
    if error:
        print(f"❌ Error: {error}")
        return False
    
    print(f"✅ Found {len(viral_tweets)} viral tweets")
    
    for i, tweet in enumerate(viral_tweets, 1):
        print(f"\n  Viral Tweet {i}:")
        print(f"    User: @{tweet.get('screen_name', 'unknown')}")
        print(f"    Text: {tweet.get('text', '')[:100]}...")
        print(f"    Total Engagement: {tweet.get('total_engagement', 0):,}")
    
    return True


def test_user_analysis():
    """Test user pattern analysis"""
    print_section("Testing User Pattern Analysis")
    
    scraper = TwitterScraperAdvanced()
    
    username = "elonmusk"  # Example - change to any public account
    print(f"Analyzing user: @{username}")
    
    analysis, error = scraper.analyze_user_patterns(username, tweet_limit=50)
    
    if error:
        print(f"❌ Error: {error}")
        return False
    
    print(f"✅ Analysis complete!")
    print(f"\n  Tweet Count Analyzed: {analysis['tweet_count']}")
    print(f"  Avg Likes: {analysis['avg_likes']}")
    print(f"  Avg Retweets: {analysis['avg_retweets']}")
    print(f"  Total Engagement: {analysis['total_engagement']:,}")
    print(f"  Avg Text Length: {analysis['avg_text_length']} characters")
    
    print(f"\n  Most Used Hashtags:")
    for tag in analysis['most_used_hashtags'][:5]:
        print(f"    {tag['hashtag']} ({tag['count']} times)")
    
    print(f"\n  Peak Posting Hours:")
    for hour, count in list(analysis['peak_posting_hours'].items())[:3]:
        print(f"    {hour}:00 - {count} tweets")
    
    return True


def main():
    """Run all tests"""
    print("\n" + "🚀 "*20)
    print("  TWITTER SCRAPER ENHANCED - TEST SUITE")
    print("🚀 "*20)
    
    # Check if cookies exist
    if not os.path.exists('twitter_cookies.json'):
        print("\n❌ ERROR: twitter_cookies.json not found!")
        print("   Please login first using the Trend Manager UI")
        print("   or manually import cookies.\n")
        return
    
    print("\n✅ Cookies found. Starting tests...\n")
    
    tests = [
        ("Trends with Caching", test_trends),
        ("Advanced Search", test_search_advanced),
        ("Hashtag Analysis", test_hashtag_analysis),
        ("Viral Content", test_viral_content),
        ("User Analysis", test_user_analysis),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The enhanced scraper is working!\n")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.\n")


if __name__ == "__main__":
    main()
