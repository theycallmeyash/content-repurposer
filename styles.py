import streamlit as st

def apply_custom_css():
    """Apply global CSS styles to the application"""
    st.markdown("""
    <style>
        /* Global Styles */
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
            padding: 3rem;
            margin-bottom: 2rem;
            text-align: center;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        }
        
        .gradient-text {
            background: linear-gradient(to right, #30CFD0 0%, #330867 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
            font-size: 3.5rem;
            margin-bottom: 0.5rem;
            letter-spacing: -1px;
        }
        
        .subtitle-text {
            font-size: 1.2rem;
            color: #e0e0e0;
            margin-bottom: 2rem;
            font-weight: 300;
        }
        
        .feature-tag {
            display: inline-block;
            padding: 0.4rem 1rem;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            font-size: 0.9rem;
            margin: 0 0.3rem;
            color: #ccc;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
    
        /* Platform specific styling */
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
        
        /* Tabs Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 8px 16px;
        }
        
        /* Landing Page specific */
        .landing-hero {
            text-align: center;
            padding: 5rem 1rem;
        }
        
        .cta-button {
            margin-top: 2rem;
        }
    </style>
    """, unsafe_allow_html=True)
