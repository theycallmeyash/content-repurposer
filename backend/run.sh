#!/bin/bash
echo "🚀 Starting Prism..."
export OLLAMA_MODEL="${OLLAMA_MODEL:-gemma4:26b}"
export OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
export OLLAMA_TIMEOUT="${OLLAMA_TIMEOUT:-300}"
source venv/bin/activate
streamlit run app.py
