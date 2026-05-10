# PRISM AI — Content Repurposer

A monorepo containing the full PRISM AI stack:

| Directory | Stack | Description |
|-----------|-------|-------------|
| `backend/` | Python · Streamlit · FastAPI | Scraping, LLM engine, trend analysis |
| `frontend/` | React 19 · TanStack Start · Vite · Tailwind | Web UI |

---

## Getting Started

### Backend (Streamlit App)
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
bash run.sh
```

### Frontend (React App)
```bash
cd frontend
npm install
npm run dev
```

---

## Architecture
```
content-repurposer/
├── backend/
│   ├── app.py               # Streamlit entry point
│   ├── core/                # Business logic (LLM, extractors, models)
│   ├── pages/               # Streamlit pages
│   ├── service/             # Twitter scraper & LLM analyzer
│   ├── data_engine/         # Trend scraping (Twitter, LinkedIn)
│   ├── ui/                  # Shared styles
│   ├── data/                # Persistent data (chroma, cache)
│   └── requirements.txt
└── frontend/
    ├── routes/              # TanStack Router pages
    ├── package.json
    └── vite.config.ts
```
