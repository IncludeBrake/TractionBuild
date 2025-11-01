from __future__ import annotations
from typing import List
import numpy as np
import hashlib

class Embedder:
    def encode(self, texts: List[str]) -> np.ndarray:
        raise NotImplementedError

class MockEmbedder(Embedder):
    def __init__(self, dim: int = 8):
        self.dim = dim

    def encode(self, texts: List[str]) -> np.ndarray:
        vectors = []
        for text in texts:
            # Create a deterministic vector based on the text
            seed = sum(ord(c) for c in text)
            rng = np.random.default_rng(seed)
            vec = rng.random(self.dim, dtype=np.float32)
            
            # Normalize to unit length
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec /= norm
            vectors.append(vec)
        return np.array(vectors)
