import os
import sys
import logging
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.brand_profile_engine import BrandProfileEngine
from core.content_repurposer import ContentRepurposer
from core.models import TrendContext

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_pipeline():
    print("🚀 Starting 100% LOCAL Multi-Stream Verification Pipeline...")
    print("📢 Requirement: Ollama must be running with 'llama3.1:8b' model.")

    # 1. Mock Brand History (The "Soul")
    past_posts = [
        "Infrastructure is the only thing that matters in the AI era. Everything else is just a wrapper.",
        "Scale is the only moat left. If you can't run it locally, it's not yours.",
        "Stop building landing pages and start building distribution systems. Speed is life."
    ]

    print("\n--- Phase 1: Local Brand Soul Distillation (Ollama) ---")
    soul_engine = BrandProfileEngine()
    try:
        soul = soul_engine.distill_soul(past_posts)
        print(f"✅ Distilled Soul: Tone={soul.tone}, Domain={soul.domain}")
    except Exception as e:
        print(f"❌ Distillation failed (Ollama connection?): {e}")
        return

    # 2. Setup Repurposer & Local RAG
    print("\n--- Phase 2: Local RAG Initializing (SentenceTransformers) ---")
    # Note: Repurposer still needs an API key for the final generation if using gpt/claude,
    # but for this test we are verifying the SOUL and RAG integration.
    repurposer = ContentRepurposer(api_key="local_test") 
    repurposer.vector_store.clear_database()
    repurposer.vector_store.add_posts([{"id": f"p{i}", "content": p} for i, p in enumerate(past_posts)])

    # 3. Trends & New Content
    trends = TrendContext(keywords=["Local LLMs", "NVIDIA H200"], platform="twitter")
    new_raw_content = "Researchers have found a new way to run 70B models on consumer GPUs using specialized 4-bit quantization."

    print("\n--- Phase 3: RAG Style Retrieval ---")
    examples = repurposer.vector_store.search_style_examples(new_raw_content)
    print(f"✅ Retrieved {len(examples)} style examples from local vector store.")
    for ex in examples:
        print(f"  - {ex}")

    print("\n✅ Local Pipeline Logic Verified!")

if __name__ == "__main__":
    verify_pipeline()
