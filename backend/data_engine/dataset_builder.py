import json
import logging
from typing import List, Dict, Optional
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatasetBuilder:
    """
    Transforms raw content into training datasets (Alpaca/Instruction format).
    Target Format:
    {
        "instruction": "Write a tweet about [topic] in the style of [brand]",
        "input": "[Topic Context / Trends]",
        "output": "[Actual Post Content]"
    }
    """
    
    def __init__(self, output_path: str = "data/training_data.jsonl"):
        self.output_path = output_path
        self.data = []

    def add_entry(self, instruction: str, input_text: str, output_text: str):
        """
        Add a single training example.
        """
        entry = {
            "instruction": instruction,
            "input": input_text,
            "output": output_text
        }
        self.data.append(entry)

    def process_raw_posts(self, posts: List[Dict], brand_name: str):
        """
        Ingest raw posts and auto-generate instructions.
        Expected post format: {"content": str, "platform": str, "metrics": dict (optional)}
        """
        for post in posts:
            content = post.get("content")
            if not content:
                continue
                
            platform = post.get("platform", "social media")
            
            # Heuristic: If content is short (<280), assume tweet.
            # We construct a generic instruction for now. 
            # In a real scenario, we might use a small LLM to reverse-engineer the "topic" from the post.
            
            instruction = f"Write a {platform} post in the style of {brand_name}."
            
            # Input is currently empty because we are doing "style copying". 
            # Or we could put the first sentence as input and ask to complete it?
            # For now, let's leave input empty implies "Generate from scratch/internal knowledge".
            # BUT, for repurposing, we usually have a source.
            
            # Strategy: Self-Supervised. 
            # We don't have the "source" article that generated this tweet. 
            # So we frame it as: "Here is a style."
            
            self.add_entry(
                instruction=instruction,
                input_text="", 
                output_text=content
            )
            
    def export(self):
        """
        Write data to JSONL
        """
        logger.info(f"Exporting {len(self.data)} items to {self.output_path}")
        try:
            with open(self.output_path, 'w') as f:
                for entry in self.data:
                    f.write(json.dumps(entry) + "\n")
            logger.info("Export complete.")
        except Exception as e:
            logger.error(f"Failed to export dataset: {e}")

if __name__ == "__main__":
    # Test
    builder = DatasetBuilder(output_path="test_dataset.jsonl")
    sample_posts = [
        {"content": "Just shipped a new feature! 🚀 #coding", "platform": "Twitter"},
        {"content": "Deep work is the superpower of the 21st century.", "platform": "LinkedIn"}
    ]
    builder.process_raw_posts(sample_posts, "IndieHacker")
    builder.export()
