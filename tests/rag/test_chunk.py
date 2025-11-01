from src.tractionbuild.rag.chunk import normalize, split_structural, reflow
def test_deterministic_boundaries():
    text = """## H1
Para one.

Para two with bullets:
- a
- b"""
    pieces = reflow(split_structural(normalize(text)), tokens_per_chunk=10, overlap=2)
    again  = reflow(split_structural(normalize(text)), tokens_per_chunk=10, overlap=2)
    assert [p.sha1 for p in pieces] == [p.sha1 for p in again]