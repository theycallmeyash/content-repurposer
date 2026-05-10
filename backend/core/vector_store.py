import chromadb
from chromadb.utils import embedding_functions
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class BrandVectorStore:
    def __init__(self, db_path: str = "data/chroma_db", model_name: str = "all-MiniLM-L6-v2"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.db_path)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=model_name
        )
            
        self.collection = self.client.get_or_create_collection(
            name="brand_voice",
            embedding_function=self.embedding_fn
        )

    def add_posts(self, posts: List[Dict[str, Any]]):
        """
        Add posts to the vector store.
        Expected format: [{"id": "...", "content": "...", "platform": "..."}]
        """
        if not posts:
            return
            
        ids = [p['id'] for p in posts]
        documents = [p['content'] for p in posts]
        metadatas = [
            {
                "platform": p.get("platform", "unknown"), 
                "brand": p.get("brand", "default")
            } for p in posts
        ]
        
        logger.info(f"Adding {len(posts)} posts to local vector store...")
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

    def search_style_examples(self, query_text: str, n_results: int = 3) -> List[str]:
        """
        Find the most relevant past posts to match a new piece of content.
        """
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            
            if results and results.get('documents'):
                return results['documents'][0]
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            
        return []

    def clear_database(self):
        """Clear all stored data"""
        try:
            self.client.delete_collection("brand_voice")
            self.collection = self.client.create_collection(
                name="brand_voice",
                embedding_function=self.embedding_fn
            )
            logger.info("Local vector database cleared.")
        except Exception as e:
            logger.error(f"Failed to clear database: {e}")

if __name__ == "__main__":
    # Test
    store = BrandVectorStore(db_path="data/test_chroma")
    store.add_posts([
        {"id": "1", "content": "I love building AI systems that actually solve real problems.", "platform": "twitter"},
        {"id": "2", "content": "The future of scaling is in local LLMs.", "platform": "linkedin"},
        {"id": "3", "content": "Don't trust the hype, verify the benchmakrs.", "platform": "twitter"}
    ])
    
    examples = store.search_style_examples("How do we scale AI models locally?")
    print("Found Local Examples:", examples)
