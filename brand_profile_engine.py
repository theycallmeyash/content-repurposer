import logging
import json
import requests
from typing import List, Dict, Any, Optional
from models import BrandSoul
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path("data/brand_souls")
DATA_DIR.mkdir(parents=True, exist_ok=True)

BRAND_SOUL_DISTILLER_PROMPT = """
You are an expert Brand Strategist and Linguistic Analyst. 
I am going to provide you with a corpus of past social media posts (Tweets/LinkedIn) from a specific creator.

Your goal is to extract the "Soul" of this brand. Specifically, I need:
1. **Tone**: Describe the overall attitude (e.g., Sarcastic, Professional, Visionary, Skeptical).
2. **Domain**: Identify the primary professional sectors they inhabit (e.g., Enterprise Software, AI Ethics, Crypto Trading).
3. **Vocabulary**: List 10-15 keywords or distinct phrases they use frequently.
4. **Style Guidelines**: 5-7 clear rules for how they write (e.g., "Always start with a hook", "Never use hashtags in the middle of sentences", "Use short, punchy paragraphs").

CORPUS OF POSTS:
{corpus}

---
IMPORTANT: You must output ONLY valid JSON that matches this schema:
{{
    "tone": "string",
    "domain": "string",
    "vocabulary": ["string"],
    "style_guidelines": ["string"]
}}
"""

class BrandProfileEngine:
    """
    Engine that takes a collection of posts and distills them into a BrandSoul profile.
    Uses local Ollama.
    """
    def __init__(self, ollama_url: str = "http://localhost:11434", model_name: str = "llama3.1:8b"):
        self.ollama_url = ollama_url
        self.model_name = model_name

    def distill_soul(self, posts: List[str]) -> BrandSoul:
        """
        Takes a list of raw post texts and returns a BrandSoul object using local Ollama.
        """
        if not posts:
            return BrandSoul(
                tone="Neutral", 
                domain="General", 
                vocabulary=[], 
                style_guidelines=["Write clearly."]
            )
            
        # Limit corpus size for local distillation
        corpus_text = "\n---\n".join(posts[:30])
        
        prompt = BRAND_SOUL_DISTILLER_PROMPT.format(corpus=corpus_text)
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": "You are a brand strategist who outputs only JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    "stream": False,
                    "format": "json"
                },
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            content = data['message']['content']
            
            # Parse JSON from content
            soul_data = json.loads(content)
            soul = BrandSoul(**soul_data)
            return soul
        except Exception as e:
            logger.error(f"Failed to distill brand soul via local Ollama: {e}")
            return BrandSoul(
                tone="Professional",
                domain="Technology",
                vocabulary=[],
                style_guidelines=["Balanced and informative."]
            )

    def save_soul(self, user_id: str, soul: BrandSoul):
        """Persists a BrandSoul to disk."""
        file_path = DATA_DIR / f"{user_id}.json"
        try:
            with open(file_path, "w") as f:
                f.write(soul.model_dump_json(indent=2))
            logger.info(f"Successfully saved brand soul for {user_id} to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save brand soul for {user_id}: {e}")

    def load_soul(self, user_id: str) -> Optional[BrandSoul]:
        """Loads a BrandSoul from disk if it exists."""
        file_path = DATA_DIR / f"{user_id}.json"
        if not file_path.exists():
            logger.warning(f"No brand soul found for {user_id}")
            return None
        
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                return BrandSoul(**data)
        except Exception as e:
            logger.error(f"Failed to load brand soul for {user_id}: {e}")
            return None

if __name__ == "__main__":
    # Quick test
    test_posts = [
        "Infrastructure is the only thing that matters in the AI era. Everything else is just a wrapper.",
        "Stop building wrappers and start building systems. The market is saturated with low-effort 'AI companies'.",
        "The real challenge isn't the model, it's the data gravity. Scale is the only moat left."
    ]
    engine = BrandProfileEngine()
    try:
        soul = engine.distill_soul(test_posts)
        print("Distilled Soul:", soul.model_dump_json(indent=2))
    except Exception as e:
        print(f"Ollama might not be running or accessible: {e}")
