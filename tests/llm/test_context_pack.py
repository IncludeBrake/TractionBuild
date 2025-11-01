from src.tractionbuild.llm.context_pack import pack_contexts

class Dummy:  # mimics ContextItem
    def __init__(self, text, score, doc_id, chunk_idx):
        self.text=text; self.score=score; self.doc_id=doc_id; self.chunk_idx=chunk_idx

def test_pack_contexts_is_deterministic():
    ctx = [Dummy("alpha "*50, 0.9, "A", 0), Dummy("beta "*50, 0.9, "A", 1), Dummy("gamma", 0.8, "B", 0)]
    b1, _ = pack_contexts(ctx, max_chars=200)
    b2, _ = pack_contexts(list(reversed(ctx)), max_chars=200)
    assert b1 == b2
