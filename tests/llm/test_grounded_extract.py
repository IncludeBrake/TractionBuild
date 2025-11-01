import json
from typing import List
from src.tractionbuild.llm import extract as ex
from src.tractionbuild.llm.schemas import ExtractEnvelope
from src.tractionbuild.rag.retrieve import ContextItem

class DummyClient:
    def __init__(self, model: str, timeout: int = 20):
        self.model = model
        self.timeout = timeout
    def complete_json(self, system: str, user: str, seed=None):
        # Always returns a grounded, cited answer for "Acme Inc"
        content = json.dumps({
            "company": "Acme Inc",
            "website": "https://acme.example",
            "topics": ["widgets"],
            "citations": ["docA:0"]
        })
        return {"id":"x", "model": self.model, "content": content, "usage":{"prompt_tokens":10, "completion_tokens":5}}

def test_grounded_success(monkeypatch):
    def retriever(q: str, k: int) -> List[ContextItem]:
        return [ContextItem(text="Acme Inc launches widgets", score=0.9, doc_id="docA", chunk_idx=0)]
    monkeypatch.setattr(ex, "JsonChatClient", lambda model, timeout=20: DummyClient(model, timeout))
    out: ExtractEnvelope = ex.extract_company_signals_grounded("Acme Inc announced new widgets.", retriever, k=1)
    assert out.ok and out.data and out.data.company == "Acme Inc"
    assert out.data.citations

def test_grounded_abstain_on_missing_citation(monkeypatch):
    class NoCiteClient(DummyClient):
        def complete_json(self, *a, **kw):
            content = json.dumps({"company": "Acme Inc", "topics": []})
            return {"id":"x","model":"gpt","content":content,"usage":{"prompt_tokens":1,"completion_tokens":1}}
    def retriever(q: str, k: int) -> List[ContextItem]:
        return [ContextItem(text="Acme Inc is in context", score=0.9, doc_id="docA", chunk_idx=0)]
    monkeypatch.setattr(ex, "JsonChatClient", lambda model, timeout=20: NoCiteClient(model, timeout))
    out = ex.extract_company_signals_grounded("Acme Inc.", retriever, k=1)
    assert not out.ok and out.abstain and "missing_citations" in out.abstain.reasons

def test_grounded_abstain_on_entity_not_in_context(monkeypatch):
    monkeypatch.setattr(ex, "JsonChatClient", lambda model, timeout=20: DummyClient(model, timeout))
    def retriever(q: str, k: int) -> List[ContextItem]:
        return [ContextItem(text="Totally unrelated company", score=0.9, doc_id="docB", chunk_idx=1)]
    out = ex.extract_company_signals_grounded("Acme Inc.", retriever, k=1)
    assert not out.ok and out.abstain and "entity_not_in_context" in out.abstain.reasons
