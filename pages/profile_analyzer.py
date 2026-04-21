import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service.twitter import TwitterProfileAnalyzer
from service.llm_analyzer import ContentLLMAnalyzer
from styles import apply_custom_css
import pandas as pd
import json

st.set_page_config(page_title="X Profile Analyzer", page_icon="🔬", layout="wide")
apply_custom_css()

# Page-specific CSS
st.markdown("""
<style>
    .profile-metric-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    .profile-metric-card:hover {
        border-color: rgba(0, 198, 255, 0.3);
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0, 114, 255, 0.15);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #00C6FF 0%, #0072FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0.5rem 0;
    }
    .metric-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #64748b;
        font-weight: 600;
    }
    .tweet-card {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 14px;
        padding: 1.25rem;
        margin-bottom: 0.75rem;
        transition: all 0.2s ease;
    }
    .tweet-card:hover {
        border-color: rgba(0, 198, 255, 0.2);
        background: rgba(30, 41, 59, 0.7);
    }
    .tweet-text {
        color: #E2E8F0;
        font-size: 0.95rem;
        line-height: 1.6;
        margin-bottom: 0.75rem;
    }
    .tweet-stats {
        display: flex;
        gap: 1.5rem;
        color: #94A3B8;
        font-size: 0.85rem;
    }
    .tweet-stats span {
        display: flex;
        align-items: center;
        gap: 4px;
    }
    .content-type-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .badge-media {
        background: rgba(139, 92, 246, 0.2);
        color: #A78BFA;
        border: 1px solid rgba(139, 92, 246, 0.3);
    }
    .badge-text {
        background: rgba(16, 185, 129, 0.2);
        color: #6EE7B7;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .badge-link {
        background: rgba(245, 158, 11, 0.2);
        color: #FCD34D;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    .insight-card {
        background: linear-gradient(135deg, rgba(0, 198, 255, 0.08) 0%, rgba(0, 114, 255, 0.08) 100%);
        border: 1px solid rgba(0, 198, 255, 0.2);
        border-radius: 16px;
        padding: 1.5rem;
    }
    .insight-title {
        font-size: 1rem;
        font-weight: 700;
        color: #00C6FF;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .insight-item {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.5rem 0;
        color: #E2E8F0;
        font-size: 0.9rem;
        border-bottom: 1px solid rgba(255,255,255,0.05);
    }
    .insight-item:last-child { border-bottom: none; }
    .winner-banner {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(52, 211, 153, 0.1) 100%);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 12px;
        padding: 1rem 1.5rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        color: #6EE7B7;
        font-weight: 600;
        font-size: 0.95rem;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

from service.twitter.scraper import TwitterScraperAdvanced

# Initialize scraper
if 'twitter_scraper' not in st.session_state:
    st.session_state.twitter_scraper = TwitterScraperAdvanced()

if 'twitter_profile_analyzer' not in st.session_state:
    st.session_state.twitter_profile_analyzer = TwitterProfileAnalyzer(st.session_state.twitter_scraper)

if 'llm_analyzer' not in st.session_state:
    st.session_state.llm_analyzer = ContentLLMAnalyzer()

st.markdown('<div class="animate-fade-in">', unsafe_allow_html=True)

# Header
st.markdown("""
<div class="glass-header">
    <div class="header-content">
        <div class="header-icon">🔬</div>
        <div>
            <h1 class="gradient-text">X PROFILE ANALYZER</h1>
            <span class="subtitle-text">Deep-dive into any X profile. Decode what makes their content go viral.</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Input section
st.markdown('<div class="section-header">🎯 TARGET PROFILE</div>', unsafe_allow_html=True)

col_input, col_size, col_btn = st.columns([2, 1, 1])

with col_input:
    username = st.text_input(
        "X Username", 
        placeholder="e.g. elonmusk (without @)",
        label_visibility="collapsed"
    )
    
with col_size:
    sample_size = st.slider("Sample Size", 20, 100, 50, step=10)

with col_btn:
    st.write("")  # spacing
    analyze_clicked = st.button("🔬 ANALYZE PROFILE", type="primary", use_container_width=True)

# Check cookies
cookies_exist = os.path.exists('twitter_cookies.json')
if not cookies_exist:
    st.markdown("""
    <div class="custom-warning">
        <div class="warning-icon">🔐</div>
        <div class="warning-content">
            <h4>Authentication Required</h4>
            <p>Please go to the <b>Trend Network → X Scraper</b> tab and import your cookies first.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Analysis

if analyze_clicked and username:
    username_clean = username.strip().lstrip('@')
    
    if not cookies_exist:
        st.error("❌ Not logged in. Please import cookies on the X Scraper tab first.")
    else:
        with st.spinner(f"🔬 Analyzing @{username_clean}'s profile ({sample_size} tweets)..."):
            analysis, error = st.session_state.twitter_profile_analyzer.analyze_user_patterns(
                username_clean, 
                tweet_limit=sample_size
            )
        
        if error:
            st.error(f"❌ {error}")
        elif analysis:
            st.success(f"✅ Analyzed {analysis['tweet_count']} tweets from @{username_clean}")
            
            # ── Overview Metrics ──
            st.markdown("---")
            st.markdown('<div class="section-header">📊 PROFILE OVERVIEW</div>', unsafe_allow_html=True)
            
            m1, m2, m3, m4 = st.columns(4)
            
            with m1:
                st.markdown(f"""
                <div class="profile-metric-card">
                    <div class="metric-label">Tweets Analyzed</div>
                    <div class="metric-value">{analysis['tweet_count']}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with m2:
                st.markdown(f"""
                <div class="profile-metric-card">
                    <div class="metric-label">Avg Likes</div>
                    <div class="metric-value">{analysis['avg_likes']:,.0f}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with m3:
                st.markdown(f"""
                <div class="profile-metric-card">
                    <div class="metric-label">Avg Retweets</div>
                    <div class="metric-value">{analysis['avg_retweets']:,.0f}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with m4:
                st.markdown(f"""
                <div class="profile-metric-card">
                    <div class="metric-label">Total Engagement</div>
                    <div class="metric-value">{analysis['total_engagement']:,}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # ── Content Type Analysis ──
            st.markdown("---")
            st.markdown('<div class="section-header">🧪 CONTENT TYPE ANALYSIS — What Goes Viral?</div>', unsafe_allow_html=True)
            
            ct_breakdown = analysis.get('content_type_breakdown', {})
            
            col_chart, col_detail = st.columns([1.2, 1])
            
            with col_chart:
                # Build chart data
                chart_data = []
                for ct, stats in ct_breakdown.items():
                    label = {'text_only': '📝 Text Only', 'media': '🖼️ Media', 'link': '🔗 Link'}.get(ct, ct)
                    chart_data.append({
                        'Type': label,
                        'Avg Likes': stats['avg_likes'],
                        'Avg Retweets': stats['avg_retweets'],
                        'Count': stats['count'],
                    })
                
                if chart_data:
                    df_chart = pd.DataFrame(chart_data)
                    st.bar_chart(df_chart.set_index('Type')[['Avg Likes', 'Avg Retweets']])
            
            with col_detail:
                for ct, stats in ct_breakdown.items():
                    badge_class = {'text_only': 'badge-text', 'media': 'badge-media', 'link': 'badge-link'}.get(ct, 'badge-text')
                    emoji = {'text_only': '📝', 'media': '🖼️', 'link': '🔗'}.get(ct, '📝')
                    label = {'text_only': 'Text Only', 'media': 'Media', 'link': 'Link'}.get(ct, ct)
                    
                    st.markdown(f"""
                    <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 1rem; margin-bottom: 0.5rem;">
                        <span class="content-type-badge {badge_class}">{emoji} {label}</span>
                        <div style="display: flex; gap: 2rem; margin-top: 0.75rem; color: #94A3B8; font-size: 0.85rem;">
                            <span><b style="color:#E2E8F0">{stats['count']}</b> tweets</span>
                            <span>❤️ <b style="color:#E2E8F0">{stats['avg_likes']}</b> avg</span>
                            <span>🔁 <b style="color:#E2E8F0">{stats['avg_retweets']}</b> avg</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Winner banner
                vi = analysis.get('viral_insights', {})
                best_type = vi.get('best_content_type', 'text_only')
                best_label = {'text_only': '📝 Text-only tweets', 'media': '🖼️ Media tweets', 'link': '🔗 Link tweets'}.get(best_type, best_type)
                st.markdown(f"""
                <div class="winner-banner">
                    🏆 <b>{best_label}</b> get the most engagement for this profile!
                </div>
                """, unsafe_allow_html=True)

            # ── Top Performing Tweets ──
            st.markdown("---")
            st.markdown('<div class="section-header">🔥 TOP PERFORMING TWEETS</div>', unsafe_allow_html=True)
            
            top_tweets = analysis.get('top_tweets', [])
            
            for i, tweet in enumerate(top_tweets, 1):
                ct = tweet.get('content_type', 'text_only')
                badge_class = {'text_only': 'badge-text', 'media': 'badge-media', 'link': 'badge-link'}.get(ct, 'badge-text')
                label = {'text_only': 'Text', 'media': 'Media', 'link': 'Link'}.get(ct, ct)
                
                with st.expander(f"#{i} — ❤️ {tweet['likes']:,}  🔁 {tweet['retweets']:,}  — {tweet['text'][:60]}..."):
                    st.markdown(f"""
                    <div class="tweet-card">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                            <span style="color: #94A3B8; font-size: 0.85rem;">@{tweet.get('screen_name', username_clean)}</span>
                            <span class="content-type-badge {badge_class}">{label}</span>
                        </div>
                        <div class="tweet-text">{tweet['text']}</div>
                        <div class="tweet-stats">
                            <span>❤️ {tweet['likes']:,}</span>
                            <span>🔁 {tweet['retweets']:,}</span>
                            <span>👁️ {tweet.get('views', 0):,}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if tweet.get('id'):
                        st.caption(f"🔗 https://x.com/{tweet.get('screen_name', username_clean)}/status/{tweet['id']}")

            # ── Posting Patterns & Viral Insights ──
            st.markdown("---")
            
            col_patterns, col_insights = st.columns([1.2, 1])
            
            with col_patterns:
                st.markdown('<div class="section-header">⏰ POSTING PATTERNS</div>', unsafe_allow_html=True)
                
                # Peak Hours
                peak_hours = analysis.get('peak_posting_hours', {})
                if peak_hours:
                    hours_df = pd.DataFrame([
                        {"Hour": f"{h}:00", "Tweets": c} 
                        for h, c in sorted(peak_hours.items())
                    ])
                    st.bar_chart(hours_df.set_index("Hour"))
                
                # Best Days
                posting_days = analysis.get('posting_days', {})
                if posting_days:
                    days_df = pd.DataFrame([
                        {"Day": d, "Tweets": c} 
                        for d, c in posting_days.items()
                    ])
                    st.bar_chart(days_df.set_index("Day"))
            
            with col_insights:
                st.markdown('<div class="section-header">💡 VIRAL INSIGHTS</div>', unsafe_allow_html=True)
                
                vi = analysis.get('viral_insights', {})
                best_type_label = {'text_only': '📝 Text-only', 'media': '🖼️ Media', 'link': '🔗 Link'}.get(vi.get('best_content_type', ''), vi.get('best_content_type', 'N/A'))
                
                st.markdown(f"""
                <div class="insight-card">
                    <div class="insight-title">🧠 What Works for @{username_clean}</div>
                    <div class="insight-item">
                        <span>🏆</span>
                        <span>Best content type: <b>{best_type_label}</b></span>
                    </div>
                    <div class="insight-item">
                        <span>⏰</span>
                        <span>Best posting hour: <b>{vi.get('best_posting_hour', 'N/A')}:00</b></span>
                    </div>
                    <div class="insight-item">
                        <span>📅</span>
                        <span>Best posting day: <b>{vi.get('best_posting_day', 'N/A')}</b></span>
                    </div>
                    <div class="insight-item">
                        <span>📏</span>
                        <span>Avg viral tweet length: <b>{vi.get('avg_viral_length', 0)} chars</b></span>
                    </div>
                    <div class="insight-item">
                        <span>📊</span>
                        <span>Avg text length: <b>{analysis.get('avg_text_length', 0)} chars</b></span>
                    </div>
                    <div class="insight-item">
                        <span>📐</span>
                        <span>Length range: <b>{analysis.get('optimal_length_range', 'N/A')}</b></span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Hashtags & Mentions
                st.markdown("")
                st.markdown('<div class="section-header">🏷️ TOP HASHTAGS</div>', unsafe_allow_html=True)
                hashtags = analysis.get('most_used_hashtags', [])
                if hashtags:
                    ht_df = pd.DataFrame(hashtags)
                    st.dataframe(ht_df, use_container_width=True, hide_index=True)
                else:
                    st.caption("No hashtags found in analyzed tweets.")
                
                st.markdown('<div class="section-header">👥 TOP MENTIONS</div>', unsafe_allow_html=True)
                mentions = analysis.get('most_mentioned', [])
                if mentions:
                    mt_df = pd.DataFrame(mentions)
                    st.dataframe(mt_df, use_container_width=True, hide_index=True)
                else:
                    st.caption("No mentions found in analyzed tweets.")

            # ── AI Strategy Recommendations ──
            st.markdown("---")
            st.markdown('<div class="section-header">🤖 AI STRATEGY RECOMMENDATIONS (Llama 3.2)</div>', unsafe_allow_html=True)
            
            with st.spinner("Analyzing profile patterns with local AI..."):
                ai_insights = st.session_state.llm_analyzer.analyze_profile(analysis)
                
            st.markdown("### ✨ PRISMAI CORE Insights & Tactics")
            st.info(ai_insights)

            # ── Trending Tweets Generator ──
            st.markdown("---")
            st.markdown('<div class="section-header">🔥 RIDE THE TRENDS (Ghostwriter)</div>', unsafe_allow_html=True)
            st.write(f"Draft viral-worthy tweets about current trends in the tone of **@{username_clean}**.")
            
            # Initialize trend caching
            if 'local_trends_cache' not in st.session_state:
                st.session_state.local_trends_cache = []
                
            col_fetch, col_sel = st.columns([1, 2])
            with col_fetch:
                if st.button("🔄 Fetch Top X Trends", use_container_width=True):
                    with st.spinner("Fetching global trends..."):
                        trends, err = st.session_state.twitter_scraper.get_trends(woeid=1)
                        if not err and trends:
                            st.session_state.local_trends_cache = [t['keyword'] for t in trends[:15]]
                            st.rerun()
                        elif err:
                            st.error(err)
            
            with col_sel:
                selected_trend = st.selectbox(
                    "Select a Trending Topic", 
                    options=st.session_state.local_trends_cache if st.session_state.local_trends_cache else ["Click Fetch to load trends..."],
                    disabled=not bool(st.session_state.local_trends_cache)
                )
            
            if st.session_state.local_trends_cache and st.button("✨ Draft Tweets in My Tone", type="primary"):
                with st.spinner(f"Scouring Twitter for '{selected_trend}' and analyzing drafts..."):
                    # We need the trend analyzer to get viral examples
                    from service.twitter.trend_analyzer import TwitterTrendAnalyzer
                    if 'twitter_trend_analyzer' not in st.session_state:
                         st.session_state.twitter_trend_analyzer = TwitterTrendAnalyzer(st.session_state.twitter_scraper)
                         
                    # Fetch top 5 tweets for the trend context
                    trend_tweets_data, err = st.session_state.twitter_trend_analyzer.find_viral_content(
                        query=selected_trend, 
                        min_engagement=100, # Lower barrier to ensure we get context
                        limit=5
                    )
                    
                    if err:
                        st.error(f"Could not fetch trend context: {err}")
                    else:
                        drafts = st.session_state.llm_analyzer.generate_trend_tweet(
                            analysis, 
                            selected_trend, 
                            trend_tweets_data
                        )
                        st.markdown(f"### ✍️ Generated Drafts for '{selected_trend}'")
                        st.success(drafts)

            # ── Export ──
            st.markdown("---")
            col_export1, col_export2, _ = st.columns([1, 1, 2])
            
            with col_export1:
                # Export top tweets as CSV
                if top_tweets:
                    export_df = pd.DataFrame(top_tweets)
                    csv = export_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "⬇️ Export Top Tweets (CSV)",
                        data=csv,
                        file_name=f"x_profile_{username_clean}_top_tweets.csv",
                        mime="text/csv"
                    )
            
            with col_export2:
                # Export full analysis as JSON
                analysis_json = json.dumps(analysis, indent=2, default=str).encode('utf-8')
                st.download_button(
                    "⬇️ Export Full Analysis (JSON)",
                    data=analysis_json,
                    file_name=f"x_profile_{username_clean}_analysis.json",
                    mime="application/json"
                )

elif analyze_clicked and not username:
    st.warning("⚠️ Please enter an X username to analyze.")

# Sidebar info
with st.sidebar:
    st.subheader("🔬 Profile Analyzer")
    st.markdown("""
    **How it works:**
    1. Enter any X/Twitter username
    2. We fetch their recent tweets
    3. Analyze engagement patterns
    4. Surface what goes viral
    
    **Requires:** X cookies imported via the Trend Network page.
    """)
    
    st.markdown("---")
    st.caption("💡 Tip: Larger sample sizes give more accurate insights but take longer to fetch.")

st.markdown('</div>', unsafe_allow_html=True)
