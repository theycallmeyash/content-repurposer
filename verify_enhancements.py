from service.twitter import TwitterTrendAnalyzer
import logging

logging.basicConfig(level=logging.INFO)

def test_enhanced_capabilities():
    analyzer = TwitterTrendAnalyzer()
    
    print("\n--- Testing Viral Content Finder ---")
    # Using a broad query that should find results easily
    try:
        viral, error = analyzer.find_viral_content("python", min_engagement=10, limit=5)
        if error:
            print(f"Error: {error}")
        else:
            print(f"Passed: Found {len(viral)} tweets. Top: {viral[0]['text'][:30]}...")
    except Exception as e:
        print(f"Viral Test Failed: {e}")

    print("\n--- Testing Hashtag Analysis ---")
    try:
        analysis, error = analyzer.analyze_hashtag_performance("AI", limit=5)
        if error:
            print(f"Error: {error}")
        else:
            print(f"Passed: Analysis for keys: {list(analysis.keys())}")
    except Exception as e:
        print(f"Analysis Test Failed: {e}")

if __name__ == "__main__":
    test_enhanced_capabilities()
