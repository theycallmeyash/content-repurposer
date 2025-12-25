import streamlit as st
import os
from dotenv import load_dotenv
from content_extractor import ContentExtractor
from content_repurposer import ContentRepurposer

load_dotenv()

st.set_page_config(
    page_title="AI Content Repurposer",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - consolidated and optimized
st.markdown("""
<style>
    /* Reduce top padding */
    .block-container {
        padding-top: 2rem;
    }
    
    .stAlert { padding: 1rem; margin: 1rem 0; }
    
    /* Glassmorphic Header */
    .glass-header {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 2.5rem;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
    }
    
    .gradient-text {
        background: linear-gradient(135deg, #FF6B6B 0%, #FFE66D 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 3rem;
        margin-bottom: 0.5rem;
        letter-spacing: -1px;
    }
    
    .subtitle-text {
        font-size: 1.2rem;
        color: #e0e0e0;
        margin-bottom: 1.5rem;
        font-weight: 300;
    }
    
    .feature-tag {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        font-size: 0.9rem;
        margin: 0 0.2rem;
        color: #ccc;
    }

    .platform-section { 
        background-color: #f0f2f6; 
        padding: 1.5rem; 
        border-radius: 0.5rem; 
        margin-bottom: 1rem; 
    }
    .char-counter { 
        font-size: 0.8rem; 
        color: #666; 
        text-align: right; 
        margin-top: 0.5rem; 
    }
    .free-tier-badge { 
        background-color: #ffd700; 
        color: #000; 
        padding: 0.3rem 0.6rem; 
        border-radius: 0.3rem; 
        font-size: 0.8rem; 
        font-weight: bold; 
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state with defaults
def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        'provider': 'gemini_free',
        'api_key': '',
        'extracted_content': None,
        'results': None,
        'processing': False
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ============ SIDEBAR CONFIGURATION ============
def render_sidebar():
    """Render sidebar with settings and info"""
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Provider selection
        provider = st.selectbox(
            "Choose AI Provider",
            ["gemini_free", "gemini", "claude", "openai"],
            index=0,
            help="Select 'Gemini Free' for free tier with content limits",
            key="provider_select"
        )
        st.session_state.provider = provider
        
        # Free tier badge and info
        if provider == "gemini_free":
            st.markdown('<span class="free-tier-badge">🆓 FREE TIER</span>', unsafe_allow_html=True)
            with st.expander("📊 Free Tier Details", expanded=False):
                st.info("""
                **Limits:**
                - Max 2,500 characters input
                - 15 requests per minute
                - Single optimized API call
                - Content may be truncated
                
                **Best For:**
                - Shorter articles/posts
                - Quick content tests
                - Learning the tool
                """)
        
        # API Key input based on provider
        api_key_config = {
            "claude": ("Claude API Key", "sk-ant-", "ANTHROPIC_API_KEY"),
            "openai": ("OpenAI API Key", "sk-", "OPENAI_API_KEY"),
            "gemini": ("Gemini API Key", "AIza", "GEMINI_API_KEY"),
            "gemini_free": ("Gemini API Key", "AIza", "GEMINI_API_KEY")
        }
        
        label, prefix, env_var = api_key_config[provider]
        api_key = st.text_input(
            f"{label} ({prefix}...)",
            type="password",
            value=os.getenv(env_var, ""),
            help=f"Enter your {label}",
            key="api_key_input"
        )
        st.session_state.api_key = api_key
        
        st.markdown("---")
        
        # How to Use section
        with st.expander("📚 How to Use", expanded=True):
            st.markdown("""
            1. **Enter your API key** above
            2. **Choose input type** (URL or text)
            3. **Paste content** or URL
            4. **Click "Repurpose Content"**
            5. **Copy optimized results!**
            """)
        
        # Supported Platforms
        with st.expander("🎯 Supported Platforms"):
            st.markdown("""
            - 🐦 **Twitter Threads** (280 chars each)
            - 💼 **LinkedIn Posts** (professional tone)
            - 📸 **Instagram Captions** (with hashtags)
            - 📝 **TL;DR Summaries** (quick overview)
            """)
        
        # Tips for best results
        with st.expander("💡 Pro Tips"):
            st.markdown("""
            **Free Tier:**
            - Keep content under 2,500 chars
            - Use for blog posts, not books
            - Single API call = faster results
            
            **Paid Tiers:**
            - Handle longer content
            - Multiple optimized calls
            - Better quality outputs
            """)

render_sidebar()

# ============ MAIN HEADER (Glassmorphic) ============
st.markdown("""
<div class="glass-header">
    <div style="font-size: 4rem; margin-bottom: 1rem;">🚀</div>
    <div class="gradient-text">AI Content Repurposer</div>
    <div class="subtitle-text">Transform your long-form content into platform-optimized posts in seconds.</div>
    <div style="margin-top: 1.5rem;">
        <span class="feature-tag">🐦 Twitter Threads</span>
        <span class="feature-tag">💼 LinkedIn Posts</span>
        <span class="feature-tag">📸 Instagram</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ============ MAIN CONTENT AREA ============
col1, col2 = st.columns([1, 1])

# ============ LEFT COLUMN: INPUT ============
with col1:
    st.header("📥 Input Content")
    
    # Input type selector
    input_type = st.selectbox(
        "Select Input Type",
        ["Blog Post URL", "YouTube Video URL", "Raw Text"],
        help="Choose where your content is coming from",
        key="input_type_select"
    )
    
    # Determine input mode
    input_mode_map = {
        "Raw Text": "text",
        "YouTube Video URL": "youtube",
        "Blog Post URL": "blog"
    }
    input_mode = input_mode_map[input_type]
    
    # Input field based on type
    if input_type == "Raw Text":
        user_input = st.text_area(
            "Paste your content here",
            height=300,
            placeholder="Paste your blog post, article, or any text content here...",
            key="raw_text_input"
        )
        
        # Character count and warning for free tier
        if user_input:
            char_count = len(user_input)
            col_count, col_status = st.columns([2, 1])
            
            with col_count:
                st.caption(f"📊 Character count: **{char_count:,}**")
            
            with col_status:
                if st.session_state.provider == "gemini_free" and char_count > 2500:
                    st.warning("⚠️ Will truncate")
                elif char_count > 2500:
                    st.success("✅ OK")
    else:
        placeholder = "https://example.com/article" if "Blog" in input_type else "https://youtube.com/watch?v=..."
        user_input = st.text_input(
            f"Enter {input_type}",
            placeholder=placeholder,
            key="url_input"
        )
    
    # Extract button for URLs (only show for URL inputs)
    if input_type != "Raw Text":
        st.markdown("---")
        
        if st.button("📖 Extract Content", use_container_width=True, type="secondary", key="extract_btn"):
            if not user_input:
                st.error("❌ Please enter a URL first!")
            else:
                with st.spinner("📖 Extracting content from URL..."):
                    extractor = ContentExtractor()
                    content, error = extractor.extract_content(user_input, input_mode)
                    
                    if error:
                        st.error(f"❌ {error}")
                        st.session_state.extracted_content = None
                    else:
                        st.session_state.extracted_content = content
                        char_count = len(content)
                        st.success(f"✅ Extracted **{char_count:,}** characters")
                        
                        # Free tier warning
                        if st.session_state.provider == "gemini_free" and char_count > 2500:
                            st.info(f"ℹ️ Content will be truncated to 2,500 characters for free tier")
        
        # Show preview of extracted content
        if st.session_state.extracted_content:
            with st.expander("👁️ Preview Extracted Content", expanded=False):
                preview = st.session_state.extracted_content[:500]
                if len(st.session_state.extracted_content) > 500:
                    preview += "..."
                st.text_area(
                    "Content Preview",
                    value=preview,
                    height=150,
                    disabled=True,
                    key="content_preview"
                )
    
    st.markdown("---")
    
    # Main repurpose button
    process_button = st.button(
        "🚀 Repurpose Content", 
        type="primary", 
        use_container_width=True,
        disabled=st.session_state.processing,
        key="process_btn"
    )

# ============ RIGHT COLUMN: OUTPUT ============
with col2:
    st.header("📤 Generated Content")
    
    # Check for API key
    if not st.session_state.api_key:
        st.warning(f"⚠️ Please enter your **{st.session_state.provider.upper()}** API key in the sidebar to get started.")
        st.info("👈 Configure your settings in the sidebar")
    
    # Process content when button is clicked
    elif process_button:
        if not user_input:
            st.error("❌ Please provide some content to repurpose!")
        else:
            st.session_state.processing = True
            
            # For URL inputs, use extracted content; for text, use direct input
            if input_type != "Raw Text":
                if not st.session_state.extracted_content:
                    st.warning("⚠️ Please extract content first using the 'Extract Content' button")
                    st.session_state.processing = False
                    st.stop()
                content = st.session_state.extracted_content
            else:
                content = user_input
            
            # Show processing info
            char_count = len(content)
            
            # Free tier info
            if st.session_state.provider == "gemini_free":
                if char_count > 2500:
                    st.info(f"🆓 Free tier: Truncating **{char_count:,}** chars → **2,500** chars")
                else:
                    st.info(f"🆓 Free tier: Using **single optimized** API call")
            
            # Repurpose content
            with st.spinner("🤖 Repurposing content with AI... This may take 30-60 seconds"):
                try:
                    repurposer = ContentRepurposer(
                        provider=st.session_state.provider, 
                        api_key=st.session_state.api_key
                    )
                    
                    results = repurposer.repurpose_content(content)
                    st.session_state.results = results
                    st.success("✅ Content repurposed successfully!")
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.session_state.results = None
                
                finally:
                    st.session_state.processing = False

# ============ RESULTS DISPLAY ============
if st.session_state.results:
    st.markdown("---")
    st.header("✨ Your Repurposed Content")
    
    results = st.session_state.results
    
    # Create tabs for different platforms
    tab1, tab2, tab3, tab4 = st.tabs(["🐦 Twitter", "💼 LinkedIn", "📸 Instagram", "📝 TL;DR"])
    
    with tab1:
        st.subheader("Twitter Thread")
        tweets = results.get('twitter_thread', [])
        
        if tweets:
            st.info(f"Generated **{len(tweets)}** tweets for your thread")
            
            for i, tweet in enumerate(tweets, 1):
                with st.container():
                    col_tweet, col_copy = st.columns([5, 1])
                    
                    with col_tweet:
                        st.text_area(
                            f"Tweet {i}/{len(tweets)}",
                            value=tweet,
                            height=100,
                            key=f"tweet_{i}",
                            label_visibility="collapsed"
                        )
                        
                        # Character count with color coding
                        char_len = len(tweet)
                        color = "green" if char_len <= 280 else "red"
                        st.markdown(
                            f"<div class='char-counter' style='color: {color};'>"
                            f"{char_len}/280 characters</div>", 
                            unsafe_allow_html=True
                        )
                    
                    with col_copy:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("📋", key=f"copy_tweet_{i}", help="Copy to clipboard"):
                            st.toast(f"Tweet {i} copied!", icon="✅")
        else:
            st.warning("⚠️ No tweets generated. Try again or check your content.")
    
    with tab2:
        st.subheader("LinkedIn Post")
        linkedin_post = results.get('linkedin_post', '')
        
        if linkedin_post:
            st.text_area(
                "Professional LinkedIn Post", 
                value=linkedin_post, 
                height=300, 
                key="linkedin_post",
                label_visibility="collapsed"
            )
            st.markdown(
                f"<div class='char-counter'>{len(linkedin_post):,} characters</div>", 
                unsafe_allow_html=True
            )
            
            if st.button("📋 Copy LinkedIn Post", key="copy_linkedin"):
                st.toast("LinkedIn post copied!", icon="✅")
        else:
            st.warning("⚠️ No LinkedIn post generated.")
    
    with tab3:
        st.subheader("Instagram Caption")
        instagram_caption = results.get('instagram_caption', '')
        
        if instagram_caption:
            st.text_area(
                "Instagram Caption with Hashtags", 
                value=instagram_caption, 
                height=200, 
                key="instagram_caption",
                label_visibility="collapsed"
            )
            
            # Count hashtags
            hashtag_count = instagram_caption.count('#')
            st.caption(f"📊 {hashtag_count} hashtags included")
            
            if st.button("📋 Copy Instagram Caption", key="copy_instagram"):
                st.toast("Instagram caption copied!", icon="✅")
        else:
            st.warning("⚠️ No Instagram caption generated.")
    
    with tab4:
        st.subheader("TL;DR Summary")
        tldr = results.get('tldr', '')
        
        if tldr:
            st.text_area(
                "Quick Summary", 
                value=tldr, 
                height=150, 
                key="tldr",
                label_visibility="collapsed"
            )
            
            if st.button("📋 Copy TL;DR", key="copy_tldr"):
                st.toast("TL;DR copied!", icon="✅")
        else:
            st.warning("⚠️ No TL;DR generated.")
    
    # Core analysis in expander
    with st.expander("🔍 View Core Content Analysis", expanded=False):
        core = results.get('core_analysis', 'No analysis available')
        st.markdown(core)
    
    # Download all button
    st.markdown("---")
    col_download, col_clear = st.columns(2)
    
    with col_download:
        # Create downloadable text file
        download_content = f"""AI CONTENT REPURPOSER - RESULTS
{'='*50}

TWITTER THREAD:
{'-'*50}
"""
        for i, tweet in enumerate(results.get('twitter_thread', []), 1):
            download_content += f"\n{i}. {tweet}\n"
        
        download_content += f"""
LINKEDIN POST:
{'-'*50}
{results.get('linkedin_post', '')}

INSTAGRAM CAPTION:
{'-'*50}
{results.get('instagram_caption', '')}

TL;DR:
{'-'*50}
{results.get('tldr', '')}

CORE ANALYSIS:
{'-'*50}
{results.get('core_analysis', '')}
"""
        
        st.download_button(
            label="📥 Download All Content",
            data=download_content,
            file_name="repurposed_content.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    with col_clear:
        if st.button("🗑️ Clear Results", use_container_width=True):
            st.session_state.results = None
            st.session_state.extracted_content = None
            st.rerun()

# ============ FOOTER ============
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p>Built with ❤️ using AI & Streamlit</p>
    <p style='font-size: 0.8rem;'>
        Save hours of content repurposing time • Maintain your message across platforms
    </p>
    <p style='font-size: 0.7rem; margin-top: 1rem;'>
        💡 <strong>Tip:</strong> Start with the free tier, upgrade when you need more capacity
    </p>
</div>
""", unsafe_allow_html=True)