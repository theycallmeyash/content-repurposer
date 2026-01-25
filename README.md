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

## 🆕 New Updates
### 📈 Trend Manager & Engine
A powerful new engine to fetch real-time trending topics to inspire your content creation.
- **Multi-Source Intelligence**: Fetches trends from **X (Twitter)**, **LinkedIn** (via API or Apify), and **Reddit**.
- **X.com Scraper 2.0**:
    - **Manual Cookie Import**: Bypass Cloudflare blocks and 403 errors by safely importing browser cookies.
    - **Standalone HTTP/2 Client**: Robust fetching mechanism that mimics a real browser.
    - **Local Caching**: Saves trends locally to minimize API calls and avoid rate limits.
- **Unified Dashboard**: View, filter, and manage trends from all sources in one glassmorphic interface.

### 💎 Prism Studio Refactor
- **Architecture**: Split into a robust Multi-Page App (Home, Studio, Trend Manager, Settings).
- **Visuals**: Enhanced "Glassmorphism" UI with dynamic gradients, floating animations, and a customized component system.

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

4. **Configure API Keys**
   - Copy `.env.example` to `.env`
   - Add your API keys (Gemini, LinkedIn, etc.)

5. **Twitter/X Scraper Setup (Crucial)**
   To enable Twitter trend fetching, you must import your browser cookies to avoid bot detection:
   1. Install the **[Cookie-Editor](https://cookie-editor.com/)** browser extension.
   2. Log in to `x.com` in your browser.
   3. Open the extension -> Click **Export** -> **Export as JSON**.
   4. Go to the **Trend Manager** page in Prism.
   5. Select the **🐦 X Scraper** tab -> **Manual Cookies**.
   6. Paste the JSON and click **Import**.
   *Note: This creates a `twitter_cookies.json` file locally. Do not share this file.*

## 🗺️ Roadmap

### Phase 1: The Core (Completed)
- [x] **Rebranding**: Transition to "Prism" identity.
- [x] **Architecture**: Split into Multi-Page App.
- [x] **Trend Engine**: Real-time fetching from X and LinkedIn.
- [ ] **Smart Previews**: Visual mockups (Twitter Card / LinkedIn UI).

### Phase 2: Advanced Studio (Upcoming)
- [ ] **Black Box Decryptor**: Interactive logs and security visualization.
- [ ] **Voice Engine**: Analyze previous posts to create a custom "Brand Voice" profile.
- [ ] **Visual Studio**: Integrated AI image generation.
- [ ] **Scheduler Integration**: One-click scheduling.

## 📄 License
MIT License. Built with ❤️ using Streamlit & AI.
