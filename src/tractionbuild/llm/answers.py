from __future__ import annotations
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from src.tractionbuild.llm.schemas import ExtractEnvelope
from src.tractionbuild.rag.retrieve import ContextItem

class Citation(BaseModel):
    chunk_id: str | None = None
    doc_id: str | None = None
    chunk_idx: int | None = None
    sha1: str | None = None
    label: str | None = None  # e.g., "A:3" as stable short ref

class Answer(BaseModel):
    company: str | None = None
    website: str | None = None
    topics: List[str] = Field(default_factory=list)

class AnswerEnvelope(BaseModel):
    ok: bool
    answer: Answer | None = None
    abstained: bool = False
    reasons: List[str] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)  # timing, model, budgets

def _mk_labels(cites: List[Dict[str, Any]]) -> List[Citation]:
    out: List[Citation] = []
    for c in cites:
        doc = c.get("doc_id")
        idx = c.get("chunk_idx")
        label = f"{doc}:{idx}" if doc is not None and idx is not None else None
        out.append(Citation(
            chunk_id=c.get("chunk_id"),
            doc_id=doc,
            chunk_idx=idx,
            sha1=c.get("sha1"),
            label=label,
        ))
    return out

def compose_answer(
    extract: ExtractEnvelope,
    ctx_items: List[ContextItem] | None,
    model_latency_ms: float | None = None,
    p95_ms: float | None = None,
    token_usage: Dict[str, int] | None = None,
) -> AnswerEnvelope:
    """
    Deterministic composer:
    - If extractor abstained/failed => propagate abstention + reasons.
    - Else map fields to Answer and stitch resolved citations (if present in raw).
    - Never include raw PII; citations only expose doc_id/chunk_idx/sha1.
    """
    if not extract.ok or extract.abstain:
        reasons = (extract.abstain.reasons if extract.abstain else []) or ["extract_failed"]
        return AnswerEnvelope(
            ok=False, abstained=True, reasons=reasons, meta={"model": extract.model, "usage": extract.usage}
        )

    resolved = []
    raw = extract.raw or {}
    if "resolved_citations" in raw and isinstance(raw["resolved_citations"], list):
        resolved = raw["resolved_citations"]

    ans = Answer(
        company=getattr(extract.data, "company", None),
        website=getattr(extract.data, "website", None),
        topics=(getattr(extract.data, "topics", None) or []),
    )

    cites = _mk_labels(resolved)
    meta = {
        "model": extract.model,
        "usage": extract.usage,
        "latency_ms": model_latency_ms,
        "p95_ms": p95_ms,
        "ctx_count": len(ctx_items or []),
    }
    return AnswerEnvelope(ok=True, answer=ans, citations=cites, meta=meta)