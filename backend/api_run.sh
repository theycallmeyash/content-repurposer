#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")"
export OLLAMA_MODEL="${OLLAMA_MODEL:-gemma4:26b}"
export OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
export OLLAMA_TIMEOUT="${OLLAMA_TIMEOUT:-300}"

if [ -f "../venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source ../venv/bin/activate
elif [ -f "venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source venv/bin/activate
fi

uvicorn api:app --host 127.0.0.1 --port 8788 --reload
