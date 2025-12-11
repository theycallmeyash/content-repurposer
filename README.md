# AI Content Repurposer

Small Streamlit app scaffold for extracting content and repurposing it into
other formats (summary, tweet, blog, bullets).

Quick start

1. Create a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and add any API keys you have.

3. Run the Streamlit app:

```bash
streamlit run app.py
```

Notes
- `content_repurposer.py` contains a placeholder for Claude integration; the
  real API call is intentionally left as a TODO. The app will fall back to
  a local repurposer when no key is provided.
- `content_extractor.py` provides basic HTML paragraph extraction and simple
  file reading. You can extend it to use richer extractors (YouTube, PDFs).
