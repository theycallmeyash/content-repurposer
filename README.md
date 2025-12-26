# 💎 Prism | AI Content Repurposer

> **Refract your best work.**
> Transform deep-dive content (Blogs, Videos) into infinite social assets using AI.

Prism is a **Creator Studio** that takes your "Core Asset" (a long-form blog post or YouTube video) and intelligently repurposes it for Twitter, LinkedIn, and Instagram.

## 🚀 Features (MVP)
- **Multi-Source Input**: Accepts YouTube URLs, Blog URLs, or Raw Text.
- **Intelligent Extraction**: Automatically scrapes and cleans content.
- **Platform Optimization**:
    - 🐦 **Twitter Threads**: Punchy, threaded tweets under 280 chars.
    - 💼 **LinkedIn**: Professional, engagement-focused posts.
    - 📸 **Instagram**: Visual captions with hashtag optimization.
- **Glassmorphic UI**: A premium, distraction-free workspace.
- **Free Tier**: Optimized for Gemini Free API (no credit card needed).

## 🗺️ Roadmap

### Phase 1: The Core (Current)
- [x] **Rebranding**: Transition to "Prism" identity.
- [x] **Architecture**: Split into Multi-Page App (Home, Studio, Settings).
- [ ] **Smart Previews**: Visual mockups of how posts will look on actual platforms (Twitter Card / LinkedIn UI).
- [ ] **Hook Laboratory**: Generate 5 variations of the "first line" to maximize scroll-stopping power.

### Phase 2: Advanced Studio (Upcoming)
- [ ] **Voice Engine**: Analyze your previous posts to create a custom "Brand Voice" profile.
- [ ] **Visual Studio**: Integrated AI image generation for Instagram/LinkedIn posts.
- [ ] **Scheduler Integration**: One-click scheduling to Buffer/Typefully.
- [ ] **Analytics**: Track content performance (future).

## 🛠️ Setup & Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/prism.git
   cd prism
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   streamlit run app.py
   ```

4. **Configure API**
   - Go to the **Settings** page.
   - Enter your Gemini (Free), OpenAI, or Claude API key.

## 📄 License
MIT License. Built with ❤️ using Streamlit & AI.
