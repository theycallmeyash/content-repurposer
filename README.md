# 💎 Prism | Sovereign AI Content Repurposer

> **Refract your best work. Locally.**
> Transform deep-dive content (Blogs, Videos) into infinite social assets using private, local AI.

Prism is a **Sovereign Creator Studio** that takes your "Core Asset" (a long-form blog post or YouTube video) and intelligently repurposes it for Twitter, LinkedIn, and Instagram. Unlike generic AI tools, Prism runs entirely on your hardware, preserving your privacy and your unique brand voice.

## 🚀 Key Achievements: The "Sovereign AI" Shift

This week, we successfully transitioned from cloud-dependent APIs to a fully local, high-performance content engine. 

### 🧠 The 3-Stream Architecture
The core engine now balances three distinct influences to ensure every post is factual, authentic, and timely:

1.  **Content Stream**: Strips the raw factual "meat" from your video transcripts and long-form blogs using local Llama 3.1.
2.  **Soul Stream (Brand Identity)**: Uses **Local RAG** to analyze your past content. It builds a vector database of *your* voice, injecting your personality into every output.
3.  **Trend Stream**: (In-Progress) Real-time platform signals and "virality" hooks to ensure your content hits the right discoverability notes.

### 🛡️ Privacy & Performance
-   **Local LLM Core**: Powered by **Llama 3.1 (8B)** via Ollama. No data leaves your machine.
-   **Local Embeddings**: High-speed retrieval using `sentence-transformers` (all-MiniLM-L6-v2).
-   **Zero API Costs**: No per-post fees or subscription taxes.

## 🛠️ Tech Stack
-   **Orchestration**: Python, Streamlit
-   **Models**: Llama 3.1 (8B) via Ollama
-   **Embeddings**: Sentence Transformers
-   **Vector Store**: Local FAISS / Chroma
-   **UI**: Premium Glassmorphic Design

## ⚙️ Setup & Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/prism.git
   cd prism
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Ollama**
   Download and install [Ollama](https://ollama.com/), then pull the required model:
   ```bash
   ollama pull llama3.1
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

## 🗺️ Roadmap

### Phase 1: The Foundation (Completed)
- [x] **Local AI Migration**: Replaced Gemini/Cloud APIs with local models.
- [x] **3-Stream Architecture**: Implementation of Content and Soul streams.
- [x] **Brand Voice Discovery**: Distill identity from past posts via local RAG.

### Phase 2: Advanced Studio (Upcoming)
- [ ] **Trend Intelligence**: Connecting live scrapers to the Trend Stream.
- [ ] **Balance Sliders**: Granular control over Content vs. Soul vs. Trend weights.
- [ ] **Visual Studio**: Integrated local image generation for social assets.

## 📄 License
MIT License. Built with ❤️ for the Sovereign Creator.

