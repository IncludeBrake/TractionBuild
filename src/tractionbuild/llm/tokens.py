from __future__ import annotations
import os
from typing import Iterable

# Optional accurate counting via tiktoken; fallback to heuristic (≈4 chars/token)
_USE_TIKTOKEN = False
try:
    import tiktoken  # type: ignore
    _enc = tiktoken.get_encoding("cl100k_base")
    _USE_TIKTOKEN = True
except Exception:
    _enc = None

def count_tokens(text: str) -> int:
    if _USE_TIKTOKEN and _enc:
        return len(_enc.encode(text))
    # simple fallback to avoid new dependency breakage
    # empirical average ~ 4 chars/token for English
    return max(1, (len(text) + 3) // 4)

def budget_pack(snippets: Iterable[str], max_tokens: int, per_snippet_hard_cap: int = 800) -> list[str]:
    """Greedy pack by tokens with a per-snippet char cap."""
    kept, used = [], 0
    for s in snippets:
        s = s[:per_snippet_hard_cap]
        t = count_tokens(s)
        if used + t > max_tokens:
            break
        kept.append(s)
        used += t
    return kept
