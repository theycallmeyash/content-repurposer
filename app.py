import streamlit as st
from styles import apply_custom_css

# Page Config
st.set_page_config(
    page_title="Prism | Home",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply global styles
apply_custom_css()

# Landing Page Content
st.markdown("""
<div class="landing-hero">
    <div style="font-size: 6rem; margin-bottom: 1rem; animation: float 6s ease-in-out infinite;">💎</div>
    <div class="gradient-text" style="font-size: 5rem;">PRISM</div>
    <div class="subtitle-text" style="font-size: 1.5rem; max-width: 600px; margin: 0 auto;">
        Refract your deep-dive content into infinite social assets.
    </div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 1, 1])

with col2:
    if st.button("✨ Enter Prism Studio", type="primary", use_container_width=True):
        st.switch_page("pages/1_💎_Prism_Studio.py")

    st.markdown("""
    <div style="text-align: center; margin-top: 2rem; color: #666;">
        <p>Supports: Blog Posts • YouTube • Text</p>
    </div>
    """, unsafe_allow_html=True)