from __future__ import annotations
import time, os, uuid, json
from typing import Any, Dict, Optional
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import OpenAI, APITimeoutError, RateLimitError, APIError
from src.tractionbuild.core.limits import RateLimiter, LatencyWindow
from src.tractionbuild.observability.events import emit, mk_event
from src.tractionbuild.observability.metrics import record_llm_metrics

DEFAULT_TIMEOUT = 20  # seconds

_RATE = RateLimiter(capacity=5, interval_sec=1.0)    # 5 QPS ceiling
_LAT  = LatencyWindow(size=200)

class JsonChatClient:
    """
    Minimal JSON-only chat wrapper with:
    - request timeout
    - idempotency key
    - exponential retry for transient failures
    """
    def __init__(self, model: str, timeout: int = DEFAULT_TIMEOUT):
        self.model = model
        self.timeout = timeout
        self.client = OpenAI(timeout=timeout)

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=6),
        retry=retry_if_exception_type((APITimeoutError, RateLimitError, APIError)),
    )
    def complete_json(self, system: str, user: str, seed: Optional[int] = None) -> Dict[str, Any]:
        if not _RATE.allow():
            raise RateLimitError("local_rate_limit_exceeded", response=None, body=None)
        idem = str(uuid.uuid4())
        t0 = time.time()
        resp = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            seed=seed,
            response_format={"type":"json_object"},
            messages=[
                {"role":"system", "content": system},
                {"role":"user", "content": user},
            ],
            extra_headers={"Idempotency-Key": idem},
        )
        ms = (time.time() - t0) * 1000
        _LAT.add(ms)
        try:
            emit(mk_event(
                "llm.chat.complete",
                actor="JsonChatClient",
                project_id=None,
                payload={
                    "model": self.model,
                    "latency_ms": round(ms, 1),
                    "p95_ms": round(_LAT.p95(), 1),
                    "prompt_tokens": getattr(resp.usage, "prompt_tokens", 0) or 0,
                    "completion_tokens": getattr(resp.usage, "completion_tokens", 0) or 0,
                }
            ))
        except Exception:
            pass
        record_llm_metrics(self.model, ms, out["usage"]["prompt_tokens"], out["usage"]["completion_tokens"])
        # openai==1.x returns obj; coerce to python dict
        out = {
            "id": resp.id,
            "model": resp.model,
            "content": resp.choices[0].message.content or "{}",
            "usage": {
                "prompt_tokens": getattr(resp.usage, "prompt_tokens", 0) or 0,
                "completion_tokens": getattr(resp.usage, "completion_tokens", 0) or 0,
            },
        }
        return out