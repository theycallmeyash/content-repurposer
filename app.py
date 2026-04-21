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
# Landing Page Content
st.markdown("""
<div class="hero-section">
    <div style="font-size: 6rem; margin-bottom: 1rem; animation: float 6s ease-in-out infinite;">💎</div>
    <div class="gradient-text" style="font-size: 5rem;">PRISM</div>
    <div class="subtitle-text" style="max-width: 700px; margin: 0 auto;">
        <b>Refract your deep-dive content into infinite social assets.</b><br>
        The only AI repurposing engine with a soul.
    </div>
</div>
""", unsafe_allow_html=True)

# Main Action Button
col1, col2, col3 = st.columns([1, 0.8, 1])
with col2:
    if st.button("✨ ENTER PRISM STUDIO", type="primary", use_container_width=True):
        st.switch_page("pages/prism_studio.py")

# Spacer
st.markdown("<div style='height: 4rem;'></div>", unsafe_allow_html=True)

# Features Grid
col_feat1, col_feat2, col_feat3 = st.columns(3)

with col_feat1:
    st.markdown("""
    <div class="feature-card animate-slide-up" style="animation-delay: 0.1s;">
        <div class="feature-icon">🧠</div>
        <div class="feature-title">Context Aware</div>
        <div class="feature-desc">
            Uses RAG to learn from your past content. It doesn't just generate; it retrieves your unique voice and style.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_feat2:
    st.markdown("""
    <div class="feature-card animate-slide-up" style="animation-delay: 0.2s;">
        <div class="feature-icon">📈</div>
        <div class="feature-title">Trend Injected</div>
        <div class="feature-desc">
            Scrapes Twitter & LinkedIn in real-time to weave viral keywords into your content automatically.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_feat3:
    st.markdown("""
    <div class="feature-card animate-slide-up" style="animation-delay: 0.3s;">
        <div class="feature-icon">⚡</div>
        <div class="feature-title">Platform Native</div>
        <div class="feature-desc">
            Generates optimized formats for LinkedIn, X (Twitter), and Instagram with live preview editors.
        </div>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="text-align: center; margin-top: 5rem; padding: 2rem; border-top: 1px solid rgba(255,255,255,0.05); color: #64748b; font-size: 0.8rem;">
    <p>PRISM AI © 2026 • Built for Creators</p>
    <p>v2.1.0 • Stable Release</p>
</div>
""", unsafe_allow_html=True)