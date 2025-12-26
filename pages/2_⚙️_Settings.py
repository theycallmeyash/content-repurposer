import streamlit as st
import os
import sys

# Add root directory to python path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from styles import apply_custom_css

st.set_page_config(
    page_title="Settings | Prism",
    page_icon="⚙️",
    layout="wide"
)

apply_custom_css()

def init_session_state():
    """Initialize session state if accessed directly"""
    if 'provider' not in st.session_state:
        st.session_state.provider = 'gemini_free'
    if 'api_key' not in st.session_state:
        st.session_state.api_key = os.getenv('GEMINI_API_KEY', '')

init_session_state()

st.title("⚙️ Settings")
st.markdown("Configure your AI providers and application preferences.")

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 🤖 AI Provider")
    
    # Provider selection
    provider = st.selectbox(
        "Choose AI Provider",
        ["gemini_free", "gemini", "claude", "openai"],
        index=["gemini_free", "gemini", "claude", "openai"].index(st.session_state.get('provider', 'gemini_free')),
        help="Select 'Gemini Free' for free tier with content limits",
        key="settings_provider"
    )
    
    # Update session state
    st.session_state.provider = provider
    
    # Free tier badge and info
    if provider == "gemini_free":
        st.markdown('<span class="free-tier-badge">🆓 FREE TIER ACTIVE</span>', unsafe_allow_html=True)
        st.info("""
        **Free Tier Limits:**
        - Max 2,500 characters input
        - 15 requests per minute
        - Single optimized API call
        """)

    st.markdown("---")
    
    # API Key input
    api_key_config = {
        "claude": ("Claude API Key", "sk-ant-", "ANTHROPIC_API_KEY"),
        "openai": ("OpenAI API Key", "sk-", "OPENAI_API_KEY"),
        "gemini": ("Gemini API Key", "AIza", "GEMINI_API_KEY"),
        "gemini_free": ("Gemini API Key", "AIza", "GEMINI_API_KEY")
    }
    
    label, prefix, env_var = api_key_config[provider]
    
    # Get current key from state or env
    current_key = st.session_state.get('api_key', '')
    if not current_key:
        current_key = os.getenv(env_var, "")
        
    api_key = st.text_input(
        f"{label}",
        type="password",
        value=current_key,
        help=f"Enter your {label}. It starts with {prefix}...",
        placeholder=f"{prefix}..."
    )
    
    if api_key != st.session_state.get('api_key'):
        st.session_state.api_key = api_key
        st.toast("API Key saved!", icon="💾")

with col2:
    st.markdown("### 📚 About Prism")
    
    with st.expander("How it works", expanded=True):
        st.markdown("""
        **Prism** takes your long-form content (Blogs, YouTube videos) and uses advanced AI to "refract" it into perfect social media posts.
        
        1. **Go to Prism Studio**
        2. **Paste your URL**
        3. **Get infinite content**
        """)
    
    with st.expander("Privacy & Security"):
        st.markdown("""
        - Your API keys are stored only in your browser session.
        - We do not store your content.
        - All processing happens on the fly.
        """)
