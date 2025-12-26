import streamlit as st

def apply_custom_css():
    """Apply global CSS styles to the application"""
    st.markdown("""
    <style>
        /* Import Font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

        /* Global Styles */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        .block-container {
            padding-top: 2rem;
            max-width: 1200px;
        }
        
        /* Premium Glassmorphic Header - Compact */
        .glass-header {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-bottom: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 20px;
            padding: 2rem 1.5rem;
            margin-bottom: 2rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
            position: relative;
            overflow: hidden;
        }
        
        .header-content {
            display: flex;
            align-items: center;
            gap: 1.5rem;
            z-index: 1;
        }

        .header-icon {
            font-size: 2.5rem;
            animation: float 6s ease-in-out infinite;
        }
        
        .gradient-text {
            background: linear-gradient(135deg, #00C6FF 0%, #0072FF 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
            font-size: 2.5rem;
            margin: 0;
            letter-spacing: -1px;
            line-height: 1.2;
        }
        
        .subtitle-text {
            font-size: 0.9rem;
            color: #8b9bb4;
            display: block;
            margin-top: 0.2rem;
            font-weight: 400;
        }

        /* Journey Stepper */
        .journey-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2.5rem;
            padding: 0 1rem;
            position: relative;
        }
        
        .step-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 0.5rem;
            z-index: 2;
            width: 80px;
        }

        .step-circle {
            width: 32px;
            height: 32px;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            color: #64748b;
            font-size: 0.9rem;
            transition: all 0.3s ease;
        }
        
        .step-label {
            font-size: 0.75rem;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }
        
        .step-item.active .step-circle {
            background: #0072FF;
            color: white;
            border-color: #0072FF;
            box-shadow: 0 0 15px rgba(0, 114, 255, 0.4);
        }
        
        .step-item.active .step-label {
            color: #fff;
        }

        .step-line {
            flex-grow: 1;
            height: 2px;
            background: rgba(255,255,255,0.05);
            margin: 0 -10px;
            margin-bottom: 20px; /* Align with circle center roughly */
            z-index: 1;
        }

        /* Stats Card */
        .stats-card {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 1rem;
            margin-top: 1rem;
            display: flex;
            justify-content: space-around;
        }
        
        .stat-item {
            text-align: center;
        }
        
        .stat-value {
            font-size: 1.2rem;
            font-weight: 700;
            color: #fff;
        }
        
        .stat-label {
            font-size: 0.7rem;
            color: #64748b;
            text-transform: uppercase;
        }

        /* Custom Alert/Warning Box */
        .custom-warning {
            background: rgba(40, 25, 5, 0.6);
            border-left: 4px solid #F59E0B;
            padding: 1.5rem;
            border-radius: 8px;
            margin: 1.5rem 0;
            display: flex;
            align-items: center;
            gap: 1rem;
            border: 1px solid rgba(245, 158, 11, 0.1);
        }
        
        .warning-icon {
            font-size: 1.5rem;
        }

        .warning-content h4 {
            color: #F59E0B;
            margin: 0 0 0.2rem 0;
            font-size: 1rem;
            font-weight: 600;
        }

        .warning-content p {
            color: #D1D5DB;
            margin: 0;
            font-size: 0.9rem;
        }

        /* Streamlit Widget Styling */
        .stTextInput > div > div > input, 
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div > div {
            background-color: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            color: #fff;
            padding: 0.5rem;
            transition: all 0.2s;
        }

        .stTextInput > div > div > input:focus, 
        .stTextArea > div > div > textarea:focus,
        .stSelectbox > div > div > div:focus-within {
            border-color: #0072FF;
            box-shadow: 0 0 0 2px rgba(0, 114, 255, 0.2);
            background-color: rgba(255, 255, 255, 0.05);
        }

        /* Input/Output Sections */
        .section-header {
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: #64748b;
            margin-bottom: 1rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        /* Button Styling */
        div.stButton > button {
            border-radius: 12px;
            padding: 0.5rem 2rem;
            font-weight: 600;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-size: 0.9rem;
        }

        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #00C6FF 0%, #0072FF 100%);
            border: none;
            box-shadow: 0 4px 15px rgba(0, 114, 255, 0.3);
        }
        
        div.stButton > button[kind="primary"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 114, 255, 0.4);
        }

        /* Tabs Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 20px;
            background-color: transparent;
            padding-bottom: 10px;
        }

        .stTabs [data-baseweb="tab"] {
            background-color: transparent;
            border: none;
            color: #64748b;
            padding-bottom: 10px;
        }

        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            color: #00C6FF;
            border-bottom: 2px solid #00C6FF;
        }

        
    </style>
    
    """, unsafe_allow_html=True)
