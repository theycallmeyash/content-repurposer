import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_engine.trend_scraper_v2 import TrendScraperV2
from data_engine.linkedin_trend_fetcher import LinkedInTrendFetcher
from service.twitter import TwitterScraperAdvanced, TwitterTrendAnalyzer
import json
import pandas as pd
import time

st.set_page_config(page_title="Trend Manager", page_icon="📈", layout="wide")

# Initialize scrapers
if 'scraper' not in st.session_state:
    st.session_state.scraper = TrendScraperV2()

if 'linkedin_fetcher' not in st.session_state:
    st.session_state.linkedin_fetcher = LinkedInTrendFetcher(api_provider="official")

if 'twitter_scraper' not in st.session_state:
    # Upgrade to Advanced Scraper
    st.session_state.twitter_scraper = TwitterScraperAdvanced()

if 'twitter_trend_analyzer' not in st.session_state:
    st.session_state.twitter_trend_analyzer = TwitterTrendAnalyzer(st.session_state.twitter_scraper)

st.markdown('<div class="animate-fade-in">', unsafe_allow_html=True)

# Custom Header
st.markdown("""
<div class="glass-header">
    <div class="header-content">
        <div class="header-icon">📈</div>
        <div>
            <h1 class="gradient-text">TREND NETWORK</h1>
            <span class="subtitle-text">Pulse of the internet. Real-time signal detection.</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# Tabs
tab1, tab2, tab_deep_dive, tab_viral, tab_dataset, tab3, tab4, tab5 = st.tabs([
    "➕ Add Trends", 
    "📊 View All Trends", 
    "� Deep Dive Analysis",
    "🚀 Viral Content Finder",
    "💾 Dataset Builder",
    "�🔄 Reddit Trends", 
    "💼 LinkedIn Trends", 
    "🐦 X Scraper"
])

with tab1:
    st.subheader("Add Manual Trends")
    
    col1, col2 = st.columns(2)
    
    with col1:
        source = st.selectbox("Source Platform", ["twitter", "linkedin", "instagram", "other"])
    
    with col2:
        st.write("")  # Spacing
    
    trends_input = st.text_area(
        "Enter trends (one per line)",
        placeholder="AI Agents 2026\nLLM Fine-tuning\nStartup Growth Hacks",
        height=200
    )
    
    if st.button("Save Trends", type="primary"):
        if trends_input.strip():
            trends_list = [t.strip() for t in trends_input.split('\n') if t.strip()]
            st.session_state.scraper.add_manual_trends(trends_list, source=source)
            st.success(f"Added {len(trends_list)} trends from {source}")
        else:
            st.warning("Please enter at least one trend")

with tab2:
    st.subheader("All Cached Trends")
    
    all_trends = st.session_state.scraper.get_all_trends()
    
    if all_trends:
        # Group by source
        sources = {}
        for trend in all_trends:
            src = trend.get('source', 'unknown')
            if src not in sources:
                sources[src] = []
            sources[src].append(trend)
        
        # Display by source
        for source, trends in sources.items():
            st.markdown(f"### {source.upper()}")
            for t in trends:
                st.markdown(f"""
                <div class="trend-card animate-slide-up">
                    <div class="trend-header">
                        <span class="trend-keyword">{t['keyword']}</span>
                        <span style="font-size: 0.8rem; color: #64748b;">{t.get('timestamp', 'Just now')}</span>
                    </div>
                    <div class="trend-meta" style="font-size: 0.9rem; color: #94A3B8;">
                        Engagement: {t.get('engagement', 'N/A')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Clear button
        if st.button("🗑️ Clear All Trends", type="secondary"):
            st.session_state.scraper.clear_cache()
            st.rerun()
    else:
        st.info("No trends cached yet. Add some manually or fetch from Reddit!")

with tab_deep_dive:
    st.subheader("🔍 Deep Dive Analysis")
    st.markdown("Analyze a specific trend or keyword to understand its performance and related topics.")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        analyze_query = st.text_input("Enter Trend/Hashtag to Analyse", placeholder="#AI or Artificial Intelligence")
    with col2:
        analyze_limit = st.number_input("Sample Size", min_value=10, max_value=100, value=50)
        
    if st.button("🔎 Analyze Trend"):
        if analyze_query:
            with st.spinner(f"analyzing {analyze_query}..."):
                analysis, error = st.session_state.twitter_trend_analyzer.analyze_hashtag_performance(
                    analyze_query, limit=analyze_limit
                )
                
                if error:
                    st.error(error)
                else:
                    # DEBUG: Trace analysis data
                    print(f"DEBUG: Deep Dive Analysis for '{analyze_query}': {json.dumps(analysis, default=str)[:500]}...")
                    
                    # Display metrics
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Total Engagement", f"{analysis['total_engagement']:,}")
                    m2.metric("Avg Likes", analysis.get('avg_likes', 0))
                    m3.metric("Verified Users", f"{analysis['verified_percentage']}%")
                    m4.metric("Tweet Count", analysis['tweet_count'])
                    
                    # Top Related
                    st.markdown("### 🔗 Related Hashtags")
                    tags_df = pd.DataFrame(analysis['top_related_hashtags'])
                    st.dataframe(tags_df, use_container_width=True)
                    
                    # Peak Hours chart
                    st.markdown("### ⏰ Peak Posting Hours")
                    hours_data = [{"Hour": k, "Count": v} for k, v in analysis['peak_hours'].items()]
                    if hours_data:
                        st.bar_chart(pd.DataFrame(hours_data).set_index("Hour"))
                    else:
                        st.write("No peak hours data available.")   

with tab_viral:
    st.subheader("🚀 Viral Content Finder")
    st.markdown("Find high-performing content in any niche to model and repurpose.")
    
    with st.form("viral_form"):
        col1, col2 = st.columns(2)
        with col1:
            niche_query = st.text_input("Niche / Topic", placeholder="e.g. SaaS Marketing, python coding, indie hacker")
        with col2:
            min_likes = st.number_input("Min. Likes", min_value=100, value=1000, step=100)
            
        submitted = st.form_submit_button("🔥 Find Viral Tweets")
        
        if submitted and niche_query:
            with st.spinner(f"scouring for viral content in '{niche_query}'..."):
                viral_tweets, error = st.session_state.twitter_trend_analyzer.find_viral_content(
                    query=niche_query,
                    min_engagement=min_likes,
                    limit=20
                )
                
                if error:
                    st.error(error)
                elif not viral_tweets:
                    st.warning("No viral tweets found matching these strict criteria. Try lowering the min likes.")
                else:
                    print(f"DEBUG: Viral Content: Found {len(viral_tweets)} tweets for '{niche_query}'")
                    st.success(f"Found {len(viral_tweets)} viral tweets!")
                    
                    for t in viral_tweets:
                        with st.expander(f"❤️ {t.get('total_engagement', 0)}: {t['text'][:50]}..."):
                            st.write(t['text'])
                            st.caption(f"By @{t['screen_name']} | {t['created_at']}")
                            st.code(t['text'], language="text")
                            if st.button("Add to Trends", key=f"add_{t['id']}"):
                                st.session_state.scraper.add_manual_trends([t['text']], source="viral_finder")
                                st.toast("Added to trends!")

with tab_dataset:
    st.subheader("💾 Dataset Builder")
    st.markdown("Bulk fetch tweets for multiple keywords to build a dataset for analysis.")
    
    dataset_keywords = st.text_area("Enter Keywords (one per line)", height=150)
    tweets_per_keyword = st.number_input("Tweets per keyword", 10, 100, 20)
    
    if st.button("📦 Build & Export Dataset"):
        if dataset_keywords.strip():
            keywords = [k.strip() for k in dataset_keywords.split('\n') if k.strip()]
            all_data = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, kw in enumerate(keywords):
                status_text.text(f"Fetching data for: {kw}...")
                tweets, _ = st.session_state.twitter_scraper.search_tweets_advanced(kw, limit=tweets_per_keyword)
                
                for t in tweets:
                    t['keyword'] = kw # Tag with keyword
                    all_data.append(t)
                
                progress_bar.progress((i + 1) / len(keywords))
            
            status_text.text("✅ Collection Complete!")
            
            if all_data:
                df = pd.DataFrame(all_data)
                
                # Flatten nested dicts for CSV export if needed
                # For now just dump main fields
                export_df = pd.DataFrame({
                    'keyword': df['keyword'],
                    'text': df['text'],
                    'views': df['user'].apply(lambda x: x.get('followers_count', 0)), # Placeholder mapping
                    'likes': df['engagement'].apply(lambda x: x.get('likes', 0)),
                    'retweets': df['engagement'].apply(lambda x: x.get('retweets', 0)),
                    'created_at': df['created_at'],
                    'url': df['id'].apply(lambda x: f"https://x.com/i/web/status/{x}")
                })
                
                csv = export_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="⬇️ Download Dataset (CSV)",
                    data=csv,
                    file_name=f"twitter_dataset_{int(time.time())}.csv",
                    mime="text/csv"
                )
                
                st.write(f"Collected total {len(all_data)} tweets.")
            else:
                st.warning("No data collected.")
        else:
            st.error("Please enter keywords.")

with tab3:
    st.subheader("Fetch from Reddit")
    
    subreddits_input = st.text_input(
        "Subreddits (comma-separated)",
        value="technology,programming,startups,entrepreneur"
    )
    
    limit = st.slider("Posts per subreddit", 5, 50, 10)
    
    if st.button("🔄 Fetch Reddit Trends"):
        subreddits = [s.strip() for s in subreddits_input.split(',')]
        with st.spinner("Fetching from Reddit..."):
            reddit_trends = st.session_state.scraper.get_reddit_trends(subreddits=subreddits, limit=limit)
            
            if reddit_trends:
                st.success(f"Fetched {len(reddit_trends)} trends from Reddit")
                for t in reddit_trends[:10]:
                    st.markdown(f"""
                    <div class="trend-card animate-slide-up">
                        <div class="trend-header">
                            <span class="trend-keyword">{t['keyword']}</span>
                            <span style="font-size: 0.8rem; color: #F97316;">r/{t.get('subreddit', 'unknown')}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("Reddit API not configured. Using mock data.")

with tab4:
    st.subheader("Fetch from LinkedIn")
    
    st.markdown("""
    LinkedIn provides professional B2B trends. Choose your API provider:
    - **Official API**: Free tier, requires OAuth setup
    - **RapidAPI**: Easier setup, paid plans available
    - **Apify**: Pre-built scraper, $5 free credits/month
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        api_provider = st.selectbox(
            "API Provider",
            ["official", "rapidapi", "apify"],
            help="Select which API to use for fetching LinkedIn trends"
        )
    
    with col2:
        limit = st.slider("Number of trends", 5, 50, 20, key="linkedin_limit")
    
    if st.button("💼 Fetch LinkedIn Trends"):
        # Update API provider if changed
        st.session_state.linkedin_fetcher.api_provider = api_provider
        
        with st.spinner("Fetching from LinkedIn..."):
            linkedin_trends = st.session_state.linkedin_fetcher.get_all_trends(limit=limit)
            
            if linkedin_trends:
                # Add to cache
                for trend in linkedin_trends:
                    # Convert LinkedIn trend format to scraper format
                    st.session_state.scraper.trends_cache["manual"].append({
                        "keyword": trend['keyword'],
                        "source": trend['source'],
                        "timestamp": trend['timestamp'],
                        "type": "automated",
                        "engagement": trend.get('engagement', 'N/A'),
                        "hashtags": trend.get('hashtags', [])
                    })
                
                st.session_state.scraper._save_cache()
                st.success(f"✅ Fetched and cached {len(linkedin_trends)} LinkedIn trends")
                
                # Display trends
                for i, t in enumerate(linkedin_trends[:10], 1):
                    engagement = t.get('engagement', 'N/A')
                    hashtags = t.get('hashtags', [])
                    hashtag_str = " ".join([f"#{tag}" for tag in hashtags[:3]]) if hashtags else ""
                    
                    st.markdown(f"**{i}. {t['keyword']}**")
                    st.caption(f"💬 {engagement} engagements | 🏷️ {hashtag_str}")
            else:
                st.info("ℹ️ No LinkedIn trends fetched. Check your API credentials in .env file.")
    
    # API Setup Instructions
    with st.expander("📚 API Setup Instructions"):
        st.markdown("""
        ### LinkedIn Official API
        1. Go to [LinkedIn Developers](https://www.linkedin.com/developers/)
        2. Create an app and get OAuth credentials
        3. Add to `.env`: `LINKEDIN_ACCESS_TOKEN=your_token`
        
        ### RapidAPI
        1. Sign up at [RapidAPI](https://rapidapi.com/)
        2. Subscribe to LinkedIn Data API
        3. Add to `.env`: `RAPIDAPI_KEY=your_key`
        
        ### Apify
        1. Sign up at [Apify](https://apify.com/)
        2. Get your API token
        3. Add to `.env`: `APIFY_TOKEN=your_token`
        """)

with tab5:
    st.subheader("🐦 X (Twitter) Scraper")
    st.info("⚠️ Use a secondary account to avoid risk to your main profile.")
    
    col_auth, col_actions = st.columns([1, 1])
    
    with col_auth:
        st.markdown("### 🔐 Login Credentials")
        
        # Swap tabs to prioritize Manual Cookies
        login_tab1, login_tab2 = st.tabs(["🍪 Manual Cookies (Recommended)", "🤖 Auto Login (Often Blocked)"])
        
        with login_tab1:
            st.success("✅ **Best Method**: Bypasses Cloudflare blocks.")
            st.markdown("""
            **How to get cookies:**
            1. Install **[Cookie-Editor](https://cookie-editor.com/)** extension.
            2. Log in to **x.com** in your browser.
            3. Open extension -> Click **Export** (JSON) -> **Copy**.
            4. Paste below and click **Import**.
            """)
            cookie_json = st.text_area("Paste Cookies JSON", height=150, help="Paste the full list of cookies from the extension here.")
            
            if st.button("📥 Import & Save Cookies", type="primary"):
                if cookie_json:
                    success, msg = st.session_state.twitter_scraper.login_with_manual_cookies(cookie_json)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)
                else:
                     st.warning("⚠️ Please paste the JSON first.")
                            
        with login_tab2:
            st.warning("⚠️ **High Risk of 403 Block**: Automated login is easily detected by X.com.")
            st.info("Only use this if you cannot get manual cookies.")
            
            username = st.text_input("Username", placeholder="@username")
            email = st.text_input("Email", placeholder="email@example.com")
            password = st.text_input("Password", type="password")
            
            if st.button("🤖 Try Auto Login"):
                if not username or not email or not password:
                    st.error("Please fill in all fields")
                else:
                    with st.spinner("Attempting auto-login (may fail)..."):
                        success, msg = st.session_state.twitter_scraper.login(username, email, password)
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg) 
                            st.error("👇 **Please switch to 'Manual Cookies' tab above**")

    with col_actions:
        st.markdown("### 🚀 Actions")
        
        # Logout/Reset Button
        if st.button("🔄 Reset Session / Logout", type="secondary"):
             success, msg = st.session_state.twitter_scraper.logout()
             if success:
                 st.success(msg)
                 st.rerun()
             else:
                 st.error(msg)
        
        # Location Selection
        woeid_options = {
            "Global": 1,
            "United States": 23424977,
            "India": 23424848,
            "United Kingdom": 23424975,
            "Canada": 23424775,
            "Australia": 23424748,
            "Custom": 0
        }
        
        selected_location = st.selectbox("📍 Trend Location", list(woeid_options.keys()))
        
        if selected_location == "Custom":
            woeid = st.number_input("Enter Custom WOEID", value=1, step=1)
        else:
            woeid = woeid_options[selected_location]

        if st.button("🔥 Fetch Trending Topics", use_container_width=True):
            with st.spinner(f"Fetching trends for WOEID {woeid}..."):
                trends, error = st.session_state.twitter_scraper.get_trends(woeid=woeid)
                
                if error:
                    st.error(error)
                else:
                    print(f"DEBUG: Found {len(trends)} trends. Sample: {trends[:3]}") # Debug trace
                    st.success(f"✅ Found {len(trends)} trends")
                    
                    # Add to main cache automatically
                    cached_count = 0
                    for trend in trends:
                        # Convert to standard format
                        st.session_state.scraper.trends_cache["manual"].append({
                            "keyword": trend['keyword'],
                            "source": "twitter_scraper",
                            "timestamp": "Now",
                            "type": "automated",
                            "engagement": f"{trend.get('volume', 'N/A')} tweets",
                            "domain": trend.get('domain', '')
                        })
                        cached_count += 1
                    
                    st.session_state.scraper._save_cache()
                    st.toast(f"Added {cached_count} trends to your database!")
                    
                    # Display table
                    st.dataframe(trends, use_container_width=True)

        st.markdown("---")
        st.markdown("### 🔍 Search Tweets")
        search_query = st.text_input("Search Query", placeholder="e.g., 'AI Agents'")
        if st.button("Search", disabled=not search_query):
             with st.spinner(f"Searching for '{search_query}'..."):
                 tweets, error = st.session_state.twitter_scraper.search_tweets(search_query)
                 if error:
                     st.error(error)
                 else:
                     print(f"DEBUG: Search Results: {len(tweets)} tweets found.")
                     for t in tweets:
                         st.markdown(f"""
                         <div style="padding: 10px; border: 1px solid #333; border-radius: 5px; margin-bottom: 10px;">
                            <small>{t['user']['name']} (@{t['screen_name']})</small><br>
                            {t['text']}<br>
                            <small>❤️ {t['favorite_count']} | 🔁 {t['retweet_count']}</small>
                         </div>
                         """, unsafe_allow_html=True)


# Sidebar: Stats
with st.sidebar:
    st.subheader("📊 Stats")
    all_trends = st.session_state.scraper.get_all_trends()
    st.metric("Total Trends", len(all_trends))
    
    manual_count = len([t for t in all_trends if t.get('type') == 'manual'])
    reddit_count = len([t for t in all_trends if t.get('source') == 'reddit'])
    
    st.metric("Manual", manual_count)
    st.metric("Reddit", reddit_count)
    
    if st.session_state.scraper.trends_cache.get('last_updated'):
        st.caption(f"Last updated: {st.session_state.scraper.trends_cache['last_updated'][:19]}")

st.markdown('</div>', unsafe_allow_html=True) # Close fade-in div
