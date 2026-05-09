
import asyncio
import logging
import json
import httpx
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

COOKIES_PATH = 'twitter_cookies.json'

async def test_connection():
    if not os.path.exists(COOKIES_PATH):
        logger.error("No cookies found!")
        return

    saved_cookies = {}
    with open(COOKIES_PATH, 'r') as f:
        saved_cookies = json.load(f)
    
    logger.info(f"Loaded {len(saved_cookies)} cookies.")
    
    # Common Headers
    csrf_token = saved_cookies.get('ct0')
    if not csrf_token:
        logger.warning("'ct0' cookie missing!")
        
    base_headers = {
        'x-csrf-token': csrf_token,
        'x-twitter-active-user': 'yes',
        'x-twitter-auth-type': 'OAuth2Session',
        'x-twitter-client-language': 'en',
        'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    # Test Cases
    endpoints = [
        {
            'name': 'V1.1 Place Trends (api.twitter.com)',
            'url': 'https://api.twitter.com/1.1/trends/place.json',
            'params': {'id': '1'},
            'domain': '.twitter.com',
            'referer': 'https://twitter.com/'
        },
        {
            'name': 'V1.1 Place Trends (api.x.com)',
            'url': 'https://api.x.com/1.1/trends/place.json',
            'params': {'id': '1'},
            'domain': '.x.com',
            'referer': 'https://x.com/'
        },
        {
            'name': 'V2 Guide (twitter.com)',
            'url': 'https://twitter.com/i/api/2/guide.json',
            'params': {
                'include_profile_interstitial_type': '1',
                'include_blocking': '1',
                'include_blocked_by': '1',
                'include_followed_by': '1',
                'include_want_retweets': '1',
                'include_mute_edge': '1',
                'include_can_dm': '1',
                'include_can_media_tag': '1',
                'include_ext_has_nft_avatar': '1',
                'include_ext_is_blue_verified': '1',
                'include_ext_verified_type': '1',
                'skip_status': '1',
                'cards_platform': 'Web-12',
                'include_cards': '1',
                'include_ext_alt_text': 'true',
                'include_ext_limited_action_results': 'false',
                'include_quote_count': 'true',
                'include_reply_count': '1',
                'tweet_mode': 'extended',
                'include_ext_views': 'true',
                'include_entities': 'true',
                'include_user_entities': 'true',
                'include_ext_media_color': 'true',
                'include_ext_media_availability': 'true',
                'include_ext_sensitive_media_warning': 'true',
                'include_ext_trusted_friends_metadata': 'true',
                'send_error_codes': 'true',
                'simple_quoted_tweet': 'true',
                'count': '20',
                'candidate_source': 'trends',
                'include_page_configuration': 'false',
                'entity_tokens': 'false',
                'ext': 'mediaStats,highlightedLabel,hasNftAvatar,voice,enrichments,superFollowMetadata,unmentionInfo,editControl,collab_control,vibe'
            },
            'domain': '.twitter.com',
            'referer': 'https://twitter.com/'
        }
    ]

    for test in endpoints:
        logger.info(f"--- Testing {test['name']} ---")
        
        # Setup Client
        client = httpx.AsyncClient(http2=True)
        
        # Set Cookies
        for name, value in saved_cookies.items():
            client.cookies.set(name, value, domain=test['domain'])
        
        # Set Headers
        headers = base_headers.copy()
        headers['Referer'] = test['referer']
        
        try:
            response = await client.get(test['url'], params=test['params'], headers=headers)
            logger.info(f"Status: {response.status_code}")
            if response.status_code == 200:
                logger.info("SUCCESS!")
                logger.info(f"Response Preview: {response.text[:200]}")
            else:
                logger.error(f"Failed: {response.text[:200]}")
        except Exception as e:
            logger.error(f"Exception: {str(e)}")
        
        await client.aclose()
        logger.info("\n")

if __name__ == '__main__':
    asyncio.run(test_connection())
