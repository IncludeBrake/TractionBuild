from __future__ import annotations
import hashlib
from typing import List
from pydantic import BaseModel

class PackedContext(BaseModel):
    tag: str  # e.g., "C1"
    doc_id: str
    chunk_idx: int
    sha1: str
    text: str
    score: float

def deterministic_seed_from(text: str) -> int:
    return int(hashlib.sha256(text[:1024].encode("utf-8")).hexdigest()[:8], 16)

def pack_contexts(contexts, max_chars: int = 1200) -> tuple[str, List[PackedContext]]:
    """
    Deterministically order and trim contexts into a compact block.
    Sorting: by (-score, sha1) to break ties deterministically.
    """
    sorted_ctx = sorted(contexts, key=lambda c: (-c.score, getattr(c, "doc_id", ""), c.chunk_idx))
    packed: List[PackedContext] = []
    budget = max_chars
    out_lines = ["### CONTEXT"]
    for i, c in enumerate(sorted_ctx, start=1):
        tag = f"C{i}"
        snippet = c.text.strip()
        # trim aggressively if needed
        if len(snippet) > min(400, budget):
            snippet = snippet[: max(100, min(400, budget))].rsplit(" ", 1)[0] + " ..."
        entry = f"[{tag}] (doc={c.doc_id} chunk={c.chunk_idx} sha1={c.doc_id}:{c.chunk_idx})\n{snippet}"
        need = len(entry) + 2
        if need > budget and packed:
            break
        out_lines.append(entry)
        budget -= need
        packed.append(PackedContext(tag=tag, doc_id=c.doc_id, chunk_idx=c.chunk_idx,
                                    sha1=f"{c.doc_id}:{c.chunk_idx}", text=snippet, score=c.score))
    return "\n".join(out_lines), packed
