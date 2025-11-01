from __future__ import annotations
from typing import List
from .retrieve import ContextItem
from src.tractionbuild.llm.tokens import budget_pack

def pack_context(items: List[ContextItem], max_tokens: int, per_snippet_cap: int = 800) -> list[tuple[str, ContextItem]]:
    """Return [(snippet_text, item)] respecting max_tokens."""
    snippets = [ci.text for ci in items]
    kept = set(budget_pack(snippets, max_tokens=max_tokens, per_snippet_hard_cap=per_snippet_cap))
    out = []
    for ci in items:
        s = ci.text[:per_snippet_cap]
        if s in kept:
            out.append((s, ci))
            kept.remove(s)
        if not kept:
            break
    return out
