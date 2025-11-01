from __future__ import annotations
from typing import List, Dict, Any
from pydantic import BaseModel
from .chunk import normalize, split_structural, reflow, Chunk
from .embed import Embedder
from .index import MiniIndex
from .redact import Redactor

class ContextItem(BaseModel):
    text: str
    score: float
    doc_id: str
    chunk_idx: int

def prepare_corpus(doc_id: str, text: str, redactor: Redactor, embedder: Embedder, index: MiniIndex, profile="elite"):
    normalized_text = normalize(text)
    redacted_text = redactor.redact(normalized_text)
    paragraphs = split_structural(redacted_text)
    chunks = reflow(paragraphs)

    chunk_texts = [c.text for c in chunks]
    vectors = embedder.encode(chunk_texts)

    metas = [{"doc_id": doc_id, "chunk_idx": i, "sha1": c.sha1} for i, c in enumerate(chunks)]
    chunk_ids = [c.id for c in chunks]

    index.add(chunk_ids, vectors, metas, texts=chunk_texts)

def retrieve(query: str, index: MiniIndex, embedder: Embedder, redactor: Redactor, k=5, min_score=0.3, scope: Dict[str, Any] | None = None) -> List[ContextItem]:
    normalized_query = normalize(query)
    redacted_query = redactor.redact(normalized_query)
    query_vec = embedder.encode([redacted_query])[0]

    hits = index.search(query_vec, k=k, filters=scope)
    results: List[ContextItem] = []
    for hit in hits:
        if hit.score >= min_score:
            results.append(ContextItem(
                text=hit.text,
                score=hit.score,
                doc_id=hit.meta["doc_id"],
                chunk_idx=hit.meta["chunk_idx"],
            ))
    return results