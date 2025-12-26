import streamlit as st
import os
import sys

# Add root directory to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from styles import apply_custom_css
from content_extractor import ContentExtractor
from content_repurposer import ContentRepurposer

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
        'processing': False
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ============ HEADER ============
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
            st.switch_page("pages/2_⚙️_Settings.py")
    st.stop()


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
                        results = repurposer.repurpose_content(content)
                        st.session_state.results = results
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
            st.text_area("LinkedIn", value=results.get('linkedin_post', ''), height=300)
            
        with tab3:
            st.text_area("Instagram", value=results.get('instagram_caption', ''), height=200)
            
        with tab4:
             st.info(results.get('tldr', ''))
