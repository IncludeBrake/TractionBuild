import re
from typing import List, Tuple

ABSOLUTES = re.compile(r"\b(100%|always|never|guaranteed|zero risk)\b", re.I)

def simple_groundedness_eval(text: str,
                             citations: List[str] | None = None,
                             anchors: List[str] | None = None,
                             contexts: List[str] | None = None) -> Tuple[float, List[str]]:
    citations = citations or []
    anchors = anchors or []
    contexts = contexts or []
    reasons = []
    score = 0.0

    if ABSOLUTES.search(text or ""):
        reasons.append("absolute_claim")
        score += 0.2

    body = (text or "").lower()
    for a in anchors:
        a_l = a.lower().strip()
        if a_l and a_l not in body and not any(a_l in c.lower() for c in contexts):
            reasons.append(f"anchor_missing:{a}")
            score += 0.4

    if not contexts:
        reasons.append("no_context")
        score += 0.1

    return (min(score, 1.0), reasons)
