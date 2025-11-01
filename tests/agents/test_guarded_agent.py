import time
from types import SimpleNamespace
from src.tractionbuild.agents.guarded_agent import GuardedAgent
from src.tractionbuild.agents.evaluators import simple_groundedness_eval
from src.tractionbuild.core.settings import get_settings

class OkAgent:
    name="ok"
    def run(self, task, context): return {"text":"result [[1]]", "citations":[{"id":1}]}

class BadAgent:
    name="bad"
    def run(self, task, context): return {"text":"always perfect without drift", "citations":[]}

def test_quarantine_and_fallback(monkeypatch):
    s = get_settings()
    s.ANOMALY_SCORE_THRESH = 0.5
    s.CIRCUIT_OPEN_SECS = 1
    guarded = GuardedAgent(primary=BadAgent(), standby=OkAgent(), evaluator=simple_groundedness_eval, project_id="p1")
    out1 = guarded.run("t", {"anchors":["acme"]})
    assert out1["text"].startswith("result")  # fell back
    assert guarded.circuit.is_open() is True
    time.sleep(1.1)
    guarded.reinstate()
    assert guarded.circuit.is_open() is False