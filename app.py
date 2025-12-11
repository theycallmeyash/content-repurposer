"""
AI Content Repurposing Engine - MVP
Main Streamlit Application
"""

import streamlit as st
import os
from dotenv import load_dotenv
from content_extractor import ContentExtractor
from content_repurposer import ContentRepurposer

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="AI Content Repurposer",
    page_icon="🚀",
    layout="wide"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .stAlert {
        padding: 1rem;
        margin: 1rem 0;
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
</style>
""", unsafe_allow_html=True)

# Title and description
st.title("🚀 AI Content Repurposer")
st.markdown("""
Transform your long-form content into platform-optimized posts in seconds.  
**Paste a blog URL, YouTube link, or raw text → Get optimized content for Twitter, LinkedIn, Instagram, and more.**
""")

# Sidebar for API key and settings
with st.sidebar:
    st.header("⚙️ Settings")

    provider = st.selectbox(
        "Choose AI Provider",
        ["claude", "openai", "gemini"],
        index=0
    )

    if provider == "claude":
        api_key = st.text_input(
            "Claude API Key (sk-ant-...)",
            type="password",
            value=os.getenv("ANTHROPIC_API_KEY", "")
        )

    elif provider == "openai":
        api_key = st.text_input(
            "OpenAI API Key (sk-...)",
            type="password",
            value=os.getenv("OPENAI_API_KEY", "")
        )

    elif provider == "gemini":
        api_key = st.text_input(
            "Gemini API Key (AIza...)",
            type="password",
            value=os.getenv("GEMINI_API_KEY", "")
        )

    st.session_state["provider"] = provider
    st.session_state["api_key"] = api_key

    st.markdown("---")
    st.markdown("""
    ### 📚 How to Use
    1. Enter your API key
    2. Choose input type
    3. Paste URL or text
    4. Click "Repurpose Content"
    5. Copy optimized content!
    
    ### 🎯 Supported Platforms
    - Twitter Threads
    - LinkedIn Posts
    - Instagram Captions
    - TL;DR Summaries
    """)

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📥 Input Content")
    
    # Input type selector
    input_type = st.selectbox(
        "Select Input Type",
        ["Blog Post URL", "YouTube Video URL", "Raw Text"],
        help="Choose where your content is coming from"
    )
    
    # Input field based on type
    if input_type == "Raw Text":
        user_input = st.text_area(
            "Paste your content here",
            height=300,
            placeholder="Paste your blog post, article, or any text content here..."
        )
        input_mode = "text"
    else:
        user_input = st.text_input(
            f"Enter {input_type}",
            placeholder="https://example.com/article" if "Blog" in input_type else "https://youtube.com/watch?v=..."
        )
        input_mode = "youtube" if "YouTube" in input_type else "blog"
    
    # Extract button for URLs
    if input_type != "Raw Text":
        extract_button = st.button("📖 Extract Content", use_container_width=True)
        
        if extract_button and user_input:
            with st.spinner("📖 Extracting content..."):
                extractor = ContentExtractor()
                content, error = extractor.extract_content(user_input, input_mode)
                
                if error:
                    st.error(f"❌ {error}")
                else:
                    st.session_state['extracted_content'] = content
                    st.success(f"✅ Extracted {len(content)} characters")
        
        # Show extracted content if available
        if 'extracted_content' in st.session_state:
            st.text_area(
                "Extracted Content (Preview)",
                value=st.session_state['extracted_content'][:500] + "...",
                height=150,
                disabled=True
            )
    
    # Repurpose button
    process_button = st.button("🚀 Repurpose Content", type="primary", use_container_width=True)

with col2:
    st.header("📤 Generated Content")
    
    if not api_key:
        st.warning(f"⚠️ Please enter your {provider.upper()} API key in the sidebar to get started.")
    elif process_button:
        if not user_input:
            st.error("Please provide some content to repurpose!")
        else:
            # Extract content
            with st.spinner("📖 Extracting content..."):
                extractor = ContentExtractor()
                content, error = extractor.extract_content(user_input, input_mode)
                
                if error:
                    st.error(f"❌ {error}")
                else:
                    st.success(f"✅ Extracted {len(content)} characters")
            
            # Repurpose content
            if content and not error:
                with st.spinner("🤖 Repurposing content with AI... This may take 30-60 seconds"):
                    try:
                        # ✅ FIX: Pass both provider and api_key
                        repurposer = ContentRepurposer(
                            provider=st.session_state["provider"], 
                            api_key=api_key
                        )
                        results = repurposer.repurpose_content(content)
                        
                        # Store in session state
                        st.session_state['results'] = results
                        st.success("✅ Content repurposed successfully!")
                        
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

# Display results if available
if 'results' in st.session_state:
    st.markdown("---")
    st.header("✨ Your Repurposed Content")
    
    results = st.session_state['results']
    
    # Create tabs for each platform
    tab1, tab2, tab3, tab4 = st.tabs(["🐦 Twitter", "💼 LinkedIn", "📸 Instagram", "📝 TL;DR"])
    
    with tab1:
        st.subheader("Twitter Thread")
        tweets = results['twitter_thread']
        
        for i, tweet in enumerate(tweets, 1):
            col_tweet, col_copy = st.columns([5, 1])
            with col_tweet:
                st.text_area(
                    f"Tweet {i}/{len(tweets)}",
                    value=tweet,
                    height=100,
                    key=f"tweet_{i}"
                )
                st.markdown(f"<div class='char-counter'>{len(tweet)}/280 characters</div>", unsafe_allow_html=True)
            with col_copy:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("📋", key=f"copy_tweet_{i}", help="Copy to clipboard"):
                    st.code(tweet, language=None)
        
        # Copy entire thread
        full_thread = "\n\n".join([f"{i}. {tweet}" for i, tweet in enumerate(tweets, 1)])
        if st.button("📋 Copy Entire Thread", use_container_width=True):
            st.code(full_thread, language=None)
    
    with tab2:
        st.subheader("LinkedIn Post")
        linkedin_post = results['linkedin_post']
        
        st.text_area(
            "LinkedIn Post",
            value=linkedin_post,
            height=300,
            key="linkedin_post"
        )
        st.markdown(f"<div class='char-counter'>{len(linkedin_post)} characters</div>", unsafe_allow_html=True)
        
        if st.button("📋 Copy LinkedIn Post", use_container_width=True):
            st.code(linkedin_post, language=None)
    
    with tab3:
        st.subheader("Instagram Caption")
        instagram_caption = results['instagram_caption']
        
        st.text_area(
            "Instagram Caption",
            value=instagram_caption,
            height=200,
            key="instagram_caption"
        )
        
        if st.button("📋 Copy Instagram Caption", use_container_width=True):
            st.code(instagram_caption, language=None)
    
    with tab4:
        st.subheader("TL;DR Summary")
        tldr = results['tldr']
        
        st.text_area(
            "Quick Summary",
            value=tldr,
            height=150,
            key="tldr"
        )
        
        if st.button("📋 Copy TL;DR", use_container_width=True):
            st.code(tldr, language=None)
    
    # Core Analysis (collapsible)
    with st.expander("🔍 View Core Content Analysis"):
        st.markdown(results['core_analysis'])

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p>Built with ❤️ using AI & Streamlit</p>
    <p style='font-size: 0.8rem;'>Save hours of content repurposing time • Maintain your message across platforms</p>
</div>
""", unsafe_allow_html=True)