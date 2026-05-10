import csv
import json
import logging
from typing import List, Dict, Optional
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BrandDataCollector:
    """
    Ingests past content to build a 'Brand Voice' profile.
    Supports:
    - LinkedIn Export (CSV)
    - Manual JSON List
    """
    
    def __init__(self, brand_name: str):
        self.brand_name = brand_name
        self.posts = []

    def ingest_linkedin_csv(self, file_path: str):
        """
        Ingest LinkedIn posts from the standard 'Shares.csv' export.
        """
        logger.info(f"Ingesting LinkedIn CSV from: {file_path}")
        try:
            # LinkedIn export usually has 'ShareCommentary' or 'Description' columns
            df = pd.read_csv(file_path)
            
            # Common column names in exports
            content_col = None
            for col in ['ShareCommentary', 'Description', 'Content', 'Text']:
                if col in df.columns:
                    content_col = col
                    break
            
            if not content_col:
                logger.error(f"Could not find a valid content column in CSV. Available: {df.columns}")
                return
            
            count = 0
            for _, row in df.iterrows():
                content = str(row[content_col])
                if content and content != "nan":
                    self.posts.append({
                        "id": f"li_{count}",
                        "content": content,
                        "platform": "LinkedIn",
                        "brand": self.brand_name
                    })
                    count += 1
            
            logger.info(f"Ingested {count} posts from LinkedIn CSV.")
            
        except Exception as e:
            logger.error(f"Error reading CSV: {e}")

    def ingest_json(self, file_path: str):
        """
        Ingest generic JSON list of posts.
        Expected format: [{"content": "...", "platform": "..."}]
        """
        logger.info(f"Ingesting JSON from: {file_path}")
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    for idx, item in enumerate(data):
                         self.posts.append({
                            "id": f"manual_{idx}",
                            "content": item.get("content", ""),
                            "platform": item.get("platform", "Unknown"),
                            "brand": self.brand_name
                        })
                    logger.info(f"Ingested {len(data)} posts from JSON.")
        except Exception as e:
            logger.error(f"Error reading JSON: {e}")

    def get_clean_corpus(self) -> List[str]:
        """
        Returns just the text content of all ingested posts.
        """
        return [p['content'] for p in self.posts if len(p['content']) > 10]

if __name__ == "__main__":
    # Test
    collector = BrandDataCollector("MyBrand")
    
    # Create a dummy CSV for testing
    with open("test_linkedin.csv", "w") as f:
        f.write("ShareCommentary,Date,Url\n")
        f.write("\"Excited to announce our new funding round! #startup\",2023-01-01,http://...\n")
        f.write("\"Consistency is key to growth.\",2023-01-02,http://...\n")
        
    collector.ingest_linkedin_csv("test_linkedin.csv")
    print("Corpus:", collector.get_clean_corpus())
    
    # Clean up
    import os
    os.remove("test_linkedin.csv")
