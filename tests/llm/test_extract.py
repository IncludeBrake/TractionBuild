import json
import types
import builtins
import pytest

from src.tractionbuild.llm import extract as ex
from src.tractionbuild.llm.schemas import ExtractEnvelope

class DummyClient:
    def __init__(self, model: str, timeout: int = 20):
        self.model = model
        self.timeout = timeout

    def complete_json(self, system: str, user: str, seed=None):
        # Return a structured fake response
        content = json.dumps({"company": "Acme Inc", "website":"https://acme.example", "topics":["widgets"]})
        return {"id":"x", "model": self.model, "content": content, "usage":{"prompt_tokens":10, "completion_tokens":5}}

def test_extract_success(monkeypatch):
    monkeypatch.setattr(ex, "JsonChatClient", lambda model, timeout=20: DummyClient(model, timeout))
    out: ExtractEnvelope = ex.extract_company_signals("Acme Inc announced new widgets.")
    assert out.ok is True
    assert out.data is not None
    assert out.data.company == "Acme Inc"
    assert out.abstain is None

def test_extract_abstain_invalid_json(monkeypatch):
    class BadClient(DummyClient):
        def complete_json(self, *a, **kw):
            return {"id":"x","model":"gpt","content":"{not json", "usage":{"prompt_tokens":1,"completion_tokens":1}}
    monkeypatch.setattr(ex, "JsonChatClient", lambda model, timeout=20: BadClient(model, timeout))
    out = ex.extract_company_signals("unknown")
    assert out.ok is False and out.abstain is not None
    assert "invalid_json" in out.abstain.reasons

def test_extract_explicit_abstain(monkeypatch):
    class AbstainClient(DummyClient):
        def complete_json(self, *a, **kw):
            return {"id":"x","model":"gpt","content":json.dumps({"abstained": True, "reasons":["insufficient_evidence"]}),
                    "usage":{"prompt_tokens":1,"completion_tokens":1}}
    monkeypatch.setattr(ex, "JsonChatClient", lambda model, timeout=20: AbstainClient(model, timeout))
    out = ex.extract_company_signals("no company here")
    assert out.ok is False and out.abstain and out.abstain.abstained
