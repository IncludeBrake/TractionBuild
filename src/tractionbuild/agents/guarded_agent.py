import time, threading
from dataclasses import dataclass
from typing import Protocol, Any, Callable
from src.tractionbuild.core.settings import get_settings
from src.tractionbuild.observability.events import emit, mk_event

class Agent(Protocol):
    name: str
    def run(self, task: str, context: dict[str, Any]) -> dict: ...

# pluggable evaluator: returns anomaly_score in [0,1], reasons[]
EvalFn = Callable[[str, dict, dict], tuple[float, list[str]]]

@dataclass
class Circuit:
    open_until: float = 0.0
    lock: threading.Lock = threading.Lock()
    def is_open(self) -> bool:
        return time.time() < self.open_until
    def trip(self, secs: int):
        with self.lock:
            self.open_until = time.time() + secs
    def close(self):
        with self.lock:
            self.open_until = 0.0

class GuardedAgent:
    def __init__(self, primary: Agent, standby: Agent, evaluator: EvalFn, project_id: str | None):
        self.primary = primary
        self.standby = standby
        self.eval = evaluator
        self.circuit = Circuit()
        self.project_id = project_id

    @property
    def name(self): return f"Guarded({self.primary.name})"

    def run(self, task: str, context: dict) -> dict:
        s = get_settings()
        actor = self.primary.name
        # choose agent depending on circuit
        agent = self.standby if self.circuit.is_open() else self.primary
        emit(mk_event("agent.request", actor, self.project_id, {"task": task}))
        out = agent.run(task, context)  # execute
        score, reasons = self.eval(task, context, out)
        emit(mk_event("agent.response", actor, self.project_id, {"score": score, "reasons": reasons}))

        if score >= s.ANOMALY_SCORE_THRESH and agent is self.primary:
            emit(mk_event("agent.anomaly", actor, self.project_id, {"score": score, "reasons": reasons}))
            self.circuit.trip(s.CIRCUIT_OPEN_SECS)
            emit(mk_event("agent.quarantine_open", actor, self.project_id, {"until": self.circuit.open_until}))
            emit(mk_event("agent.fallback_activated", self.standby.name, self.project_id, {}))
            # return standby result immediately (rerun on standby)
            out = self.standby.run(task, context)

        return out

    # called by CI or maint op after tests pass
    def reinstate(self):
        if self.circuit.is_open():
            self.circuit.close()
            emit(mk_event("agent.quarantine_close", self.primary.name, self.project_id, {}))