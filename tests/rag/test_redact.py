from src.tractionbuild.rag.redact import Redactor

def test_redact_hash_stability():
    r = Redactor(strategy="hash", salt="x")
    t1 = r.redact("mail me at a@b.com or 444-555-6666")
    t2 = r.redact("mail me at a@b.com or 444-555-6666")
    assert t1 == t2
    assert "<email:" in t1 and "<phone:" in t1