"""
Semantic caching for TractionBuild to reduce token usage and improve performance.
"""

from cachetools import LRUCache
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import Dict, Any, Optional
import hashlib

class SemanticCache:
    """Semantic cache using sentence transformers for similarity matching."""

    def __init__(self, maxsize: int = 100):
        self.cache = LRUCache(maxsize=maxsize)
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def _get_embedding(self, text: str) -> bytes:
        """Get embedding for text and convert to bytes for hashing."""
        embedding = self.model.encode(text)
        # Convert to bytes for consistent hashing
        return embedding.tobytes()

    def _similarity_score(self, emb1: bytes, emb2: bytes) -> float:
        """Calculate cosine similarity between two embeddings."""
        arr1 = np.frombuffer(emb1, dtype=np.float32)
        arr2 = np.frombuffer(emb2, dtype=np.float32)
        dot_product = np.dot(arr1, arr2)
        norm1 = np.linalg.norm(arr1)
        norm2 = np.linalg.norm(arr2)
        return dot_product / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0.0

    def cache_result(self, project_id: str, step: str, data: Dict[str, Any]) -> str:
        """Cache a result with semantic similarity matching."""
        text_content = str(data)
        embedding = self._get_embedding(text_content)
        cache_key = f"{project_id}:{step}"

        # Store with embedding for similarity matching
        self.cache[cache_key] = {
            "data": data,
            "embedding": embedding,
            "timestamp": np.datetime64('now')
        }

        return cache_key

    def get_cached_result(self, project_id: str, step: str, query_data: Dict[str, Any], threshold: float = 0.8) -> Optional[Dict[str, Any]]:
        """Retrieve cached result if semantically similar."""
        cache_key = f"{project_id}:{step}"

        if cache_key not in self.cache:
            return None

        cached_item = self.cache[cache_key]
        query_embedding = self._get_embedding(str(query_data))
        cached_embedding = cached_item["embedding"]

        similarity = self._similarity_score(query_embedding, cached_embedding)

        if similarity >= threshold:
            return cached_item["data"]

        return None

    def clear_cache(self, project_id: Optional[str] = None):
        """Clear cache, optionally for specific project."""
        if project_id:
            keys_to_remove = [k for k in self.cache.keys() if k.startswith(f"{project_id}:")]
            for key in keys_to_remove:
                del self.cache[key]
        else:
            self.cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self.cache),
            "maxsize": self.cache.maxsize,
            "hit_rate": getattr(self.cache, 'hit_rate', 0.0)
        }

# Global cache instance
cache = SemanticCache()

# Convenience functions
def cache_result(project_id: str, step: str, data: Dict[str, Any]) -> str:
    """Cache a result."""
    return cache.cache_result(project_id, step, data)

def get_cached_result(project_id: str, step: str, query_data: Dict[str, Any], threshold: float = 0.8) -> Optional[Dict[str, Any]]:
    """Get cached result if available."""
    return cache.get_cached_result(project_id, step, query_data, threshold)
