import streamlit as st
import os
import sys

# Add root directory to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.styles import apply_custom_css
from core.content_extractor import ContentExtractor
from core.content_repurposer import ContentRepurposer
from core.brand_profile_engine import BrandProfileEngine
from data_engine.trend_scraper_v2 import TrendScraperV2
from data_engine.brand_collector import BrandDataCollector
from core.models import BrandSoul, TrendContext

st.set_page_config(
    page_title="Prism Studio",
    page_icon="💎",
    layout="wide"
)

apply_custom_css()

# Initialize session state
def init_session_state():
    defaults = {
        'provider': 'gemini_free',
        'api_key': '',
        'extracted_content': None,
        'results': None,
        'processing': False,
        'brand_soul': None,
        'selected_trends': [],
        'trend_source': 'twitter'
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ============ HEADER ============
st.markdown("""
<div class="glass-header">
    <div class="header-content">
        <div class="header-icon">💎</div>
        <div>
            <h1 class="gradient-text">PRISM STUDIO</h1>
            <span class="subtitle-text">Refract your content into infinite social assets.</span>
        </div>
    </div>
    <!-- You could add a small action button here or status indicator -->
</div>
""", unsafe_allow_html=True)

# ============ JOURNEY STEPPER ============
# Determine active step
step_1 = "active"
step_2 = "active" if st.session_state.get('extracted_content') else ""
step_3 = "active" if st.session_state.get('results') else ""
step_4 = "active" if st.session_state.get('results') else ""

st.markdown(f"""
<div class="journey-container">
    <div class="step-item {step_1}">
        <div class="step-circle">1</div>
        <div class="step-label">Source</div>
    </div>
    <div class="step-line"></div>
    <div class="step-item {step_2}">
        <div class="step-circle">2</div>
        <div class="step-label">Extract</div>
    </div>
    <div class="step-line"></div>
    <div class="step-item {step_3}">
        <div class="step-circle">3</div>
        <div class="step-label">Refract</div>
    </div>
    <div class="step-line"></div>
    <div class="step-item {step_4}">
        <div class="step-circle">4</div>
        <div class="step-label">Publish</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ============ API KEY CHECK ============
if not st.session_state.get('api_key'):
    st.markdown("""
    <div class="custom-warning">
        <div class="warning-icon">⚠️</div>
        <div class="warning-content">
            <h4>No API Key Found</h4>
            <p>The Prism needs an energy source to function. Please configure your API key in settings.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col_warn1, col_warn2, col_warn3 = st.columns([1, 2, 1])
    with col_warn2:
        if st.button("⚙️ Configure API Settings", type="primary", use_container_width=True):
            st.switch_page("pages/settings.py")
    st.stop()


# ============ SIDEBAR: BRAND SOUL & TRENDS ============
with st.sidebar:
    st.markdown("### 🎭 Brand Soul (Identity)")
    with st.expander("Distill My Soul", expanded=not st.session_state.brand_soul):
        brand_name = st.text_input("Brand Name", value="MyBrand")
        distill_method = st.radio("Distill from", ["Paste Posts", "Upload LinkedIn CSV"])
        
        if distill_method == "Paste Posts":
            corpus_text = st.text_area("Paste 5-10 recent posts", height=150, help="Newline separated")
            if st.button("✨ Distill Soul", use_container_width=True):
                if corpus_text:
                    with st.spinner("Distilling..."):
                        engine = BrandProfileEngine()
                        posts = [p.strip() for p in corpus_text.split("\n") if len(p.strip()) > 10]
                        st.session_state.brand_soul = engine.distill_soul(posts)
                        # Also add to vector store for RAG
                        repurposer = ContentRepurposer(api_key=st.session_state.api_key)
                        repurposer.vector_store.add_posts([{"id": f"manual_{i}", "content": p} for i, p in enumerate(posts)])
                        st.success("Soul Refined!")
                else:
                    st.error("Paste some posts first!")
        else:
            uploaded_file = st.file_uploader("Upload 'Shares.csv' from LinkedIn", type="csv")
            if uploaded_file:
                if st.button("🚀 Process CSV", use_container_width=True):
                    # Save temporarily
                    with open("temp_linkedin.csv", "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    collector = BrandDataCollector(brand_name)
                    collector.ingest_linkedin_csv("temp_linkedin.csv")
                    posts = collector.get_clean_corpus()
                    
                    with st.spinner("Analyzing style..."):
                        engine = BrandProfileEngine(api_key=st.session_state.api_key)
                        st.session_state.brand_soul = engine.distill_soul(posts)
                        # Add to vector store
                        repurposer = ContentRepurposer(api_key=st.session_state.api_key)
                        repurposer.vector_store.add_posts([{"id": f"li_{i}", "content": p} for i, p in enumerate(posts)])
                    
                    os.remove("temp_linkedin.csv")
                    st.success(f"Processed {len(posts)} posts!")

    if st.session_state.brand_soul:
        soul = st.session_state.brand_soul
        st.markdown(f"""
        <div style="background: rgba(102, 126, 234, 0.1); border-radius: 10px; padding: 10px; border: 1px solid #667eea;">
            <p><b>Tone:</b> {soul.tone}</p>
            <p><b>Domain:</b> {soul.domain}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🗑️ Reset Soul"):
            st.session_state.brand_soul = None
            st.rerun()

    st.markdown("---")
    st.markdown("### 📈 Viral Trends (The Spice)")
    trend_scraper = TrendScraperV2()
    
    if st.button("🔄 Sync Trends", use_container_width=True):
        with st.spinner("Fetching trends..."):
            trend_scraper.get_reddit_trends() # Supplementary Reddit trends
            st.rerun()
            
    all_trends = trend_scraper.get_all_trends()
    trend_options = [f"{t['keyword']} ({t['source']})" for t in all_trends]
    
    st.session_state.selected_trends = st.multiselect(
        "Inject Trends",
        options=trend_options,
        default=[],
        help="Select keywords to weave into your content."
    )

# ============ MAIN CONTENT AREA ============
col1, col2 = st.columns([1, 1])

# ============ LEFT COLUMN: INPUT ============
with col1:
    st.markdown('<div class="section-header">📥 INPUT SOURCE</div>', unsafe_allow_html=True)
    
    input_type = st.selectbox(
        "Source",
        ["Blog Post URL", "YouTube Video URL", "Raw Text"],
        label_visibility="collapsed"
    )
    
    input_mode_map = {
        "Raw Text": "text",
        "YouTube Video URL": "youtube",
        "Blog Post URL": "blog"
    }
    input_mode = input_mode_map[input_type]
    
    if input_type == "Raw Text":
        user_input = st.text_area(
            "Content",
            height=300,
            placeholder="Paste your content here...",
            label_visibility="collapsed"
        )
        if user_input:
            char_count = len(user_input)
            st.markdown(f"""
            <div class="stats-card">
                <div class="stat-item">
                    <div class="stat-value">{char_count:,}</div>
                    <div class="stat-label">Characters</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">~{char_count // 4:,}</div>
                    <div class="stat-label">Tokens</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        placeholder = "https://example.com/article" if "Blog" in input_type else "https://youtube.com/watch?v=..."
        user_input = st.text_input(
            "URL",
            placeholder=placeholder,
            label_visibility="collapsed"
        )
    
    # Extract Logic
    if input_type != "Raw Text":
        st.markdown("---")
        if st.button("📖 Extract Content", use_container_width=True):
            if not user_input:
                st.error("❌ Enter URL first")
            else:
                with st.spinner("Extracting..."):
                    extractor = ContentExtractor()
                    content, error = extractor.extract_content(user_input, input_mode)
                    
                    if error:
                        st.error(error)
                    else:
                        st.session_state.extracted_content = content
                        st.success(f"✅ Extracted {len(content):,} chars")

        if st.session_state.extracted_content:
            with st.expander("View Content"):
                st.text(st.session_state.extracted_content[:1000] + "...")

    st.markdown("---")
    
    process_button = st.button(
        "💎 Refract Content", 
        type="primary", 
        use_container_width=True,
        disabled=st.session_state.processing
    )

# ============ RIGHT COLUMN: OUTPUT ============
with col2:
    st.markdown('<div class="section-header">📤 GENERATED OUTPUT</div>', unsafe_allow_html=True)
    
    if process_button:
        if not user_input:
            st.error("❌ No content provided")
        else:
            # Logic for content source
            content = st.session_state.extracted_content if input_type != "Raw Text" else user_input
            
            if not content:
                 st.error("❌ Extract content first!")
            else:
                st.session_state.processing = True
                with st.spinner("💎 Refracting through the Prism..."):
                    try:
                        repurposer = ContentRepurposer(
                            provider=st.session_state.provider, 
                            api_key=st.session_state.api_key
                        )
                        
                        # Prepare Trend Context
                        trends_ctx = None
                        if st.session_state.selected_trends:
                            # Strip source from selected strings: "Trend (Source)" -> "Trend"
                            clean_keywords = [t.split(" (")[0] for t in st.session_state.selected_trends]
                            trends_ctx = TrendContext(keywords=clean_keywords, platform="multiple")
                        
                        results = repurposer.repurpose_content(
                            content, 
                            brand_soul=st.session_state.brand_soul,
                            trends=trends_ctx
                        )
                        st.session_state.results = results
                        # Initialize editable content buffers
                        st.session_state.li_content = results.get('linkedin_post', '')
                        st.balloons()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                    finally:
                        st.session_state.processing = False

    # Display Results
    if st.session_state.results:
        results = st.session_state.results
        
        tab1, tab2, tab3, tab4 = st.tabs(["🐦 Twitter", "💼 LinkedIn", "📸 Instagram", "📝 TL;DR"])
        
        with tab1:
            tweets = results.get('twitter_thread', [])
            for i, tweet in enumerate(tweets):
                st.text_area(f"Tweet {i+1}", value=tweet, height=100)
        
        with tab2:
            col_li_edit, col_li_prev = st.columns([1, 1])
            
            with col_li_edit:
                st.markdown("##### ✍️ Editor")
                # Ensure state exists
                if 'li_content' not in st.session_state:
                    st.session_state.li_content = results.get('linkedin_post', '')
                    
                st.text_area(
                    "LinkedIn Post", 
                    key="li_content", 
                    height=500,
                    label_visibility="collapsed"
                )
            
            with col_li_prev:
                st.markdown("##### 👁️ Preview")
                li_text = st.session_state.get('li_content', '')
                
                # Render Realistic Card
                st.markdown(f"""
                <div class="linkedin-card">
                    <div class="linkedin-header">
                        <div class="linkedin-avatar">P</div>
                        <div class="linkedin-info">
                            <div class="linkedin-name">Prism User</div>
                            <div class="linkedin-desc">Content Creator • 1d • <span style="font-size: 10px;">🌐</span></div>
                        </div>
                        <div style="margin-left: auto; color: #94A3B8;">•••</div>
                    </div>
                    <div class="linkedin-body">{li_text}</div>
                    <div style="padding: 0 16px; color: #94A3B8; font-size: 12px; margin-bottom: 8px;">
                        👍 88 • 4 comments
                    </div>
                    <div class="linkedin-footer">
                        <button class="linkedin-action-btn">👍 Like</button>
                        <button class="linkedin-action-btn">💬 Comment</button>
                        <button class="linkedin-action-btn">🔁 Repost</button>
                        <button class="linkedin-action-btn">🚀 Send</button>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
        with tab3:
            st.text_area("Instagram", value=results.get('instagram_caption', ''), height=200)
            
        with tab4:
             st.info(results.get('tldr', ''))
