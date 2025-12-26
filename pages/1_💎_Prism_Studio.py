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
st.markdown("""
<div class="glass-header">
    <div style="font-size: 3rem; margin-bottom: 0.5rem;">💎</div>
    <div class="gradient-text">PRISM STUDIO</div>
    <div class="subtitle-text">The workspace for your best work.</div>
</div>
""", unsafe_allow_html=True)

# ============ API KEY CHECK ============
if not st.session_state.get('api_key'):
    st.warning("⚠️ No API Key found.")
    st.info("👉 Please go to **Settings** to configure your API provider/key first.")
    if st.button("Go to Settings"):
        st.switch_page("pages/2_⚙️_Settings.py")
    st.stop()


# ============ MAIN CONTENT AREA ============
col1, col2 = st.columns([1, 1])

# ============ LEFT COLUMN: INPUT ============
with col1:
    st.header("📥 Input")
    
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
            st.caption(f"📊 Length: **{char_count:,}** chars")
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
    st.header("📤 Output")
    
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
