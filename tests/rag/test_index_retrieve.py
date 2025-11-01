import numpy as np
from src.tractionbuild.rag.index import MiniIndex
from src.tractionbuild.rag.embed import MockEmbedder

def test_rank_and_filters():
    E = MockEmbedder(dim=8)
    idx = MiniIndex(dim=8)
    texts = ["alpha", "beta", "gamma"]
    vecs = E.encode(texts)
    idx.add(["c1","c2","c3"], vecs, [{"doc_id":"A"},{"doc_id":"A"},{"doc_id":"B"}], texts=texts)
    q = E.encode(["alpha"])[0]
    hits = idx.search(q, k=2)
    assert len(hits) > 0
    assert hits[0].score > 0.9 # Similarity with itself should be close to 1.0
    assert hits[0].meta["doc_id"] in ("A","B")
    hitsB = idx.search(q, k=2, filters={"doc_id":"B"})
    assert all(h.meta["doc_id"]=="B" for h in hitsB)
    assert all(isinstance(h.text, str) and h.text for h in hits)  # returns real text
