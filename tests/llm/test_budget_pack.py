from src.tractionbuild.llm.tokens import budget_pack
from src.tractionbuild.rag.pack import pack_context
from src.tractionbuild.rag.retrieve import ContextItem

def test_budget_pack_simple():
    snippets = ["a"*100, "b"*100, "c"*100]  # ~25 tokens each with fallback
    kept = budget_pack(snippets, max_tokens=40)  # should keep ~1
    assert 1 <= len(kept) <= 2  # heuristic resilient

def test_pack_context_pairs():
    items = [ContextItem(text=f"doc{i} text " + ("x"*200), score=0.9, doc_id=f"D{i%2}", chunk_idx=i) for i in range(6)]
    pairs = pack_context(items, max_tokens=120, per_snippet_cap=120)
    assert pairs
    # returns (snippet, ContextItem) preserving order
    assert isinstance(pairs[0][1], ContextItem)
