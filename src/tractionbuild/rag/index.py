from __future__ import annotations
from typing import List, Dict, Any
import numpy as np
from pydantic import BaseModel

_EPS = 1e-8

class Hit(BaseModel):
    id: str
    score: float
    text: str
    meta: Dict[str, Any]

class MiniIndex:
    def __init__(self, dim: int):
        self.dim = dim
        self.vectors = np.empty((0, dim), dtype=np.float32)   # unit-normalized rows
        self.texts: List[str] = []
        self.metas: List[Dict[str, Any]] = []
        self.ids: List[str] = []

    def add(self, chunk_ids: List[str], vectors: np.ndarray, metas: List[Dict[str, Any]], texts: List[str]):
        # Normalize incoming vectors row-wise
        vecs = vectors.astype(np.float32, copy=True)
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        norms[norms < _EPS] = 1.0
        vecs /= norms
        self.vectors = np.vstack([self.vectors, vecs])
        self.ids.extend(chunk_ids)
        self.texts.extend(texts)
        self.metas.extend(metas)

    def search(self, query_vec: np.ndarray, k: int = 5, filters: Dict[str, Any] | None = None) -> List[Hit]:
        if not self.ids:
            return []
        q = query_vec.astype(np.float32, copy=True)
        qn = np.linalg.norm(q)
        if qn < _EPS:
            return []
        q /= qn

        idxs = list(range(len(self.ids)))
        if filters:
            idxs = [i for i, m in enumerate(self.metas) if all(m.get(k_) == v for k_, v in filters.items())]
            if not idxs:
                return []

        M = self.vectors[idxs]
        sim = M @ q
        print(f"sim: {sim}") # Print similarity scores
        k = min(k, len(idxs))
        top_local = np.argsort(sim)[-k:][::-1]
        hits: List[Hit] = []
        for li in top_local:
            gi = idxs[li]
            hits.append(Hit(id=self.ids[gi], score=float(sim[li]), text=self.texts[gi], meta=self.metas[gi]))
        return hits
