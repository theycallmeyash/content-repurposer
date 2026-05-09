import streamlit as st
import sys
import os
import re
import html

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service.twitter import TwitterProfileAnalyzer
from service.llm_analyzer import ContentLLMAnalyzer
from styles import apply_custom_css
import pandas as pd
import json

st.set_page_config(page_title="X Profile Analyzer", page_icon="🔬", layout="wide")
apply_custom_css()

# ── Security Helpers ──────────────────────────────────────────────────────────

# Absolute path to cookies file — prevents path ambiguity when CWD changes
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root (one level up from pages/)
COOKIES_PATH = os.path.join(_BASE_DIR, "twitter_cookies.json")

# Valid Twitter/X username: 1-50 alphanumeric chars + underscores only
_USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{1,50}$")


def sanitize_username(raw: str) -> tuple[str | None, str | None]:
    """
    Strip leading '@', validate format.
    Returns (clean_username, error_message).
    """
    clean = raw.strip().lstrip("@")
    if not clean:
        return None, "Username cannot be empty."
    if not _USERNAME_RE.match(clean):
        return None, (
            "Invalid username. Only letters, numbers, and underscores are allowed "
            "(max 50 characters)."
        )
    return clean, None


def safe_html(value) -> str:
    """HTML-escape any string before embedding in unsafe_allow_html blocks."""
    return html.escape(str(value), quote=True)


def sanitize_tweet_text(text: str, max_len: int = 500) -> str:
    """Escape and truncate tweet text for safe HTML rendering."""
    return safe_html(str(text)[:max_len])


def sanitize_csv_cell(value) -> str:
    """
    Prevent CSV injection: strip leading formula-trigger characters
    (=, +, -, @, TAB, CR) that spreadsheet apps may evaluate as formulas.
    """
    s = str(value)
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        s = "'" + s  # prefix with a single quote to neutralise
    return s

# ─────────────────────────────────────────────────────────────────────────────

# Page-specific CSS (no dynamic user data here — safe as-is)
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
        word-break: break-word;
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

# Header (no user data — safe)
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
        label_visibility="collapsed",
        max_chars=51,   # one over limit so validation message is clear
    )

with col_size:
    sample_size = st.slider("Sample Size", 20, 100, 50, step=10)

with col_btn:
    st.write("")
    analyze_clicked = st.button("🔬 ANALYZE PROFILE", type="primary", use_container_width=True)

# FIX: Use absolute path for cookie check (prevents CWD-relative ambiguity)
cookies_exist = os.path.exists(COOKIES_PATH)
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

    # ── FIX 1: Validate & sanitize username before any use ──
    username_clean, username_error = sanitize_username(username)
    if username_error:
        st.error(f"❌ {username_error}")
        st.stop()

    if not cookies_exist:
        st.error("❌ Not logged in. Please import cookies on the X Scraper tab first.")
    else:
        with st.spinner(f"🔬 Analyzing @{username_clean}'s profile ({sample_size} tweets)..."):
            analysis, error = st.session_state.twitter_profile_analyzer.analyze_user_patterns(
                username_clean,
                tweet_limit=sample_size
            )

        if error:
            # FIX 2: Escape error message — it may echo back user input
            st.error(f"❌ {safe_html(error)}")
        elif analysis:
            st.success(f"✅ Analyzed {int(analysis['tweet_count'])} tweets from @{username_clean}")

            # ── Overview Metrics ──
            st.markdown("---")
            st.markdown('<div class="section-header">📊 PROFILE OVERVIEW</div>', unsafe_allow_html=True)

            m1, m2, m3, m4 = st.columns(4)

            # FIX 3: All numeric values are cast to int/float — no raw API strings in HTML
            with m1:
                st.markdown(f"""
                <div class="profile-metric-card">
                    <div class="metric-label">Tweets Analyzed</div>
                    <div class="metric-value">{int(analysis['tweet_count'])}</div>
                </div>
                """, unsafe_allow_html=True)

            with m2:
                st.markdown(f"""
                <div class="profile-metric-card">
                    <div class="metric-label">Avg Likes</div>
                    <div class="metric-value">{float(analysis['avg_likes']):,.0f}</div>
                </div>
                """, unsafe_allow_html=True)

            with m3:
                st.markdown(f"""
                <div class="profile-metric-card">
                    <div class="metric-label">Avg Retweets</div>
                    <div class="metric-value">{float(analysis['avg_retweets']):,.0f}</div>
                </div>
                """, unsafe_allow_html=True)

            with m4:
                st.markdown(f"""
                <div class="profile-metric-card">
                    <div class="metric-label">Total Engagement</div>
                    <div class="metric-value">{int(analysis['total_engagement']):,}</div>
                </div>
                """, unsafe_allow_html=True)

            # ── Content Type Analysis ──
            st.markdown("---")
            st.markdown('<div class="section-header">🧪 CONTENT TYPE ANALYSIS — What Goes Viral?</div>', unsafe_allow_html=True)

            ct_breakdown = analysis.get('content_type_breakdown', {})

            col_chart, col_detail = st.columns([1.2, 1])

            # Allowed content type keys — whitelist to prevent arbitrary key injection
            _ALLOWED_CT = {"text_only", "media", "link"}
            _CT_LABELS = {'text_only': '📝 Text Only', 'media': '🖼️ Media', 'link': '🔗 Link'}
            _CT_BADGES = {'text_only': 'badge-text', 'media': 'badge-media', 'link': 'badge-link'}
            _CT_EMOJI  = {'text_only': '📝', 'media': '🖼️', 'link': '🔗'}
            _CT_SHORT  = {'text_only': 'Text Only', 'media': 'Media', 'link': 'Link'}

            with col_chart:
                chart_data = []
                for ct, stats in ct_breakdown.items():
                    if ct not in _ALLOWED_CT:   # FIX 4: whitelist content-type keys
                        continue
                    chart_data.append({
                        'Type': _CT_LABELS.get(ct, ct),
                        'Avg Likes': float(stats.get('avg_likes', 0)),
                        'Avg Retweets': float(stats.get('avg_retweets', 0)),
                        'Count': int(stats.get('count', 0)),
                    })

                if chart_data:
                    df_chart = pd.DataFrame(chart_data)
                    st.bar_chart(df_chart.set_index('Type')[['Avg Likes', 'Avg Retweets']])

            with col_detail:
                for ct, stats in ct_breakdown.items():
                    if ct not in _ALLOWED_CT:
                        continue
                    badge_class = _CT_BADGES.get(ct, 'badge-text')
                    emoji       = _CT_EMOJI.get(ct, '📝')
                    label       = _CT_SHORT.get(ct, ct)

                    st.markdown(f"""
                    <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 1rem; margin-bottom: 0.5rem;">
                        <span class="content-type-badge {badge_class}">{emoji} {label}</span>
                        <div style="display: flex; gap: 2rem; margin-top: 0.75rem; color: #94A3B8; font-size: 0.85rem;">
                            <span><b style="color:#E2E8F0">{int(stats.get('count', 0))}</b> tweets</span>
                            <span>❤️ <b style="color:#E2E8F0">{float(stats.get('avg_likes', 0))}</b> avg</span>
                            <span>🔁 <b style="color:#E2E8F0">{float(stats.get('avg_retweets', 0))}</b> avg</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                vi = analysis.get('viral_insights', {})
                best_type = vi.get('best_content_type', 'text_only')
                if best_type not in _ALLOWED_CT:    # FIX 5: sanitize best_type before HTML embed
                    best_type = 'text_only'
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
                if ct not in _ALLOWED_CT:
                    ct = 'text_only'
                badge_class = _CT_BADGES.get(ct, 'badge-text')
                label = _CT_SHORT.get(ct, ct)

                # FIX 6: Escape tweet text used in expander label and body
                tweet_text_safe = sanitize_tweet_text(tweet.get('text', ''))
                # Screen name: validate same as username
                raw_screen_name = tweet.get('screen_name', username_clean)
                screen_name_clean, _ = sanitize_username(str(raw_screen_name))
                screen_name_safe = screen_name_clean if screen_name_clean else safe_html(raw_screen_name)

                # Safe numeric values
                likes    = int(tweet.get('likes', 0))
                retweets = int(tweet.get('retweets', 0))
                views    = int(tweet.get('views', 0))
                tweet_id = tweet.get('id', '')
                # Validate tweet ID is numeric only (prevent URL injection)
                tweet_id_safe = str(tweet_id) if str(tweet_id).isdigit() else ''

                preview_text = sanitize_tweet_text(tweet.get('text', ''), max_len=60)

                with st.expander(f"#{i} — ❤️ {likes:,}  🔁 {retweets:,}  — {preview_text}..."):
                    st.markdown(f"""
                    <div class="tweet-card">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                            <span style="color: #94A3B8; font-size: 0.85rem;">@{screen_name_safe}</span>
                            <span class="content-type-badge {badge_class}">{label}</span>
                        </div>
                        <div class="tweet-text">{tweet_text_safe}</div>
                        <div class="tweet-stats">
                            <span>❤️ {likes:,}</span>
                            <span>🔁 {retweets:,}</span>
                            <span>👁️ {views:,}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # FIX 7: Only render tweet link if ID is valid numeric
                    if tweet_id_safe:
                        st.caption(f"🔗 https://x.com/{screen_name_safe}/status/{tweet_id_safe}")

            # ── Posting Patterns & Viral Insights ──
            st.markdown("---")

            col_patterns, col_insights = st.columns([1.2, 1])

            with col_patterns:
                st.markdown('<div class="section-header">⏰ POSTING PATTERNS</div>', unsafe_allow_html=True)

                peak_hours = analysis.get('peak_posting_hours', {})
                if peak_hours:
                    hours_df = pd.DataFrame([
                        {"Hour": f"{safe_html(str(h))}:00", "Tweets": int(c)}
                        for h, c in sorted(peak_hours.items())
                    ])
                    st.bar_chart(hours_df.set_index("Hour"))

                posting_days = analysis.get('posting_days', {})
                if posting_days:
                    # FIX 8: Whitelist day names to prevent arbitrary string injection
                    _VALID_DAYS = {"Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"}
                    days_df = pd.DataFrame([
                        {"Day": d, "Tweets": int(c)}
                        for d, c in posting_days.items()
                        if str(d) in _VALID_DAYS
                    ])
                    if not days_df.empty:
                        st.bar_chart(days_df.set_index("Day"))

            with col_insights:
                st.markdown('<div class="section-header">💡 VIRAL INSIGHTS</div>', unsafe_allow_html=True)

                vi = analysis.get('viral_insights', {})
                vi_best_type = vi.get('best_content_type', '')
                if vi_best_type not in _ALLOWED_CT:
                    vi_best_type = 'text_only'
                best_type_label = {'text_only': '📝 Text-only', 'media': '🖼️ Media', 'link': '🔗 Link'}.get(vi_best_type, 'N/A')

                # FIX 9: Escape all API-sourced string values going into HTML
                best_hour = safe_html(str(vi.get('best_posting_hour', 'N/A')))
                best_day  = safe_html(str(vi.get('best_posting_day',  'N/A')))
                avg_viral_len  = int(vi.get('avg_viral_length', 0))
                avg_text_len   = int(analysis.get('avg_text_length', 0))
                opt_len_range  = safe_html(str(analysis.get('optimal_length_range', 'N/A')))

                st.markdown(f"""
                <div class="insight-card">
                    <div class="insight-title">🧠 What Works for @{username_clean}</div>
                    <div class="insight-item">
                        <span>🏆</span>
                        <span>Best content type: <b>{best_type_label}</b></span>
                    </div>
                    <div class="insight-item">
                        <span>⏰</span>
                        <span>Best posting hour: <b>{best_hour}:00</b></span>
                    </div>
                    <div class="insight-item">
                        <span>📅</span>
                        <span>Best posting day: <b>{best_day}</b></span>
                    </div>
                    <div class="insight-item">
                        <span>📏</span>
                        <span>Avg viral tweet length: <b>{avg_viral_len} chars</b></span>
                    </div>
                    <div class="insight-item">
                        <span>📊</span>
                        <span>Avg text length: <b>{avg_text_len} chars</b></span>
                    </div>
                    <div class="insight-item">
                        <span>📐</span>
                        <span>Length range: <b>{opt_len_range}</b></span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("")
                st.markdown('<div class="section-header">🏷️ TOP HASHTAGS</div>', unsafe_allow_html=True)
                hashtags = analysis.get('most_used_hashtags', [])
                if hashtags:
                    # FIX 10: Render hashtags via dataframe (auto-escaped), not raw HTML
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
            st.markdown('<div class="section-header">🤖 AI STRATEGY RECOMMENDATIONS (Gemma 4)</div>', unsafe_allow_html=True)

            with st.spinner("Analyzing profile patterns with local AI..."):
                ai_insights = st.session_state.llm_analyzer.analyze_profile(analysis)

            st.markdown("### ✨ PRISMAI CORE Insights & Tactics")
            # FIX 11: Use st.info (auto-escaped) not st.markdown with raw AI output
            st.info(str(ai_insights))

            # ── Trending Tweets Generator ──
            st.markdown("---")
            st.markdown('<div class="section-header">🔥 RIDE THE TRENDS (Ghostwriter)</div>', unsafe_allow_html=True)
            st.write(f"Draft viral-worthy tweets about current trends in the tone of **@{username_clean}**.")

            if 'local_trends_cache' not in st.session_state:
                st.session_state.local_trends_cache = []

            col_fetch, col_sel = st.columns([1, 2])
            with col_fetch:
                if st.button("🔄 Fetch Top X Trends", use_container_width=True):
                    with st.spinner("Fetching global trends..."):
                        trends, err = st.session_state.twitter_scraper.get_trends(woeid=1)
                        if not err and trends:
                            # FIX 12: Escape trend keywords before caching for display
                            st.session_state.local_trends_cache = [
                                html.escape(str(t['keyword']))[:100]
                                for t in trends[:15]
                            ]
                            st.rerun()
                        elif err:
                            st.error(safe_html(str(err)))

            with col_sel:
                selected_trend = st.selectbox(
                    "Select a Trending Topic",
                    options=st.session_state.local_trends_cache if st.session_state.local_trends_cache else ["Click Fetch to load trends..."],
                    disabled=not bool(st.session_state.local_trends_cache)
                )

            if st.session_state.local_trends_cache and st.button("✨ Draft Tweets in My Tone", type="primary"):
                with st.spinner(f"Scouring Twitter for '{safe_html(selected_trend)}' and analyzing drafts..."):
                    from service.twitter.trend_analyzer import TwitterTrendAnalyzer
                    if 'twitter_trend_analyzer' not in st.session_state:
                        st.session_state.twitter_trend_analyzer = TwitterTrendAnalyzer(st.session_state.twitter_scraper)

                    trend_tweets_data, err = st.session_state.twitter_trend_analyzer.find_viral_content(
                        query=selected_trend,
                        min_engagement=100,
                        limit=5
                    )

                    if err:
                        st.error(f"Could not fetch trend context: {safe_html(str(err))}")
                    else:
                        drafts = st.session_state.llm_analyzer.generate_trend_tweet(
                            analysis,
                            selected_trend,
                            trend_tweets_data
                        )
                        st.markdown(f"### ✍️ Generated Drafts for '{safe_html(selected_trend)}'")
                        # FIX 13: Use st.success (auto-escaped) for AI output
                        st.success(str(drafts))

            # ── Export ──
            st.markdown("---")
            col_export1, col_export2, _ = st.columns([1, 1, 2])

            with col_export1:
                if top_tweets:
                    # FIX 14: Sanitize every cell to prevent CSV injection
                    safe_rows = [
                        {k: sanitize_csv_cell(v) for k, v in row.items()}
                        for row in top_tweets
                    ]
                    export_df = pd.DataFrame(safe_rows)
                    csv = export_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "⬇️ Export Top Tweets (CSV)",
                        data=csv,
                        file_name=f"x_profile_{username_clean}_top_tweets.csv",
                        mime="text/csv"
                    )

            with col_export2:
                analysis_json = json.dumps(analysis, indent=2, default=str).encode('utf-8')
                st.download_button(
                    "⬇️ Export Full Analysis (JSON)",
                    data=analysis_json,
                    file_name=f"x_profile_{username_clean}_analysis.json",
                    mime="application/json"
                )

elif analyze_clicked and not username:
    st.warning("⚠️ Please enter an X username to analyze.")

# Sidebar
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