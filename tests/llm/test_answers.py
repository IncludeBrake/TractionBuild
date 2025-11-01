from src.tractionbuild.llm.answers import compose_answer
from src.tractionbuild.llm.schemas import ExtractCompanySignals, ExtractEnvelope

def test_compose_success_with_citations():
    data = ExtractCompanySignals(company="Acme", website="https://ac.me", topics=["widgets"])
    raw = {"resolved_citations":[{"doc_id":"D1","chunk_idx":0,"sha1":"abc","chunk_id":"chunk_0_deadbeef"}]}
    env = ExtractEnvelope(ok=True, model="gpt-4o-mini", usage={"prompt_tokens":5,"completion_tokens":3}, data=data, raw=raw)
    out = compose_answer(env, ctx_items=[], model_latency_ms=120.5, p95_ms=200.0)
    assert out.ok and out.answer and out.citations
    assert out.answer.company == "Acme"
    assert out.citations[0].label == "D1:0"

def test_compose_propagates_abstain():
    env = ExtractEnvelope(ok=False, model="m", usage={}, data=None, abstain=None, raw=None)
    out = compose_answer(env, ctx_items=None)
    assert out.abstained and not out.ok