from functools import wraps
from typing import Callable, Awaitable, Any, Dict
import re, json, os

# Import metrics if available, otherwise create dummy functions
try:
    from tractionbuild.observability.metrics import ERRORS
except ImportError:
    # Dummy error counter for standalone mode
    class DummyCounter:
        def labels(self, **kwargs): return self
        def inc(self): pass
    ERRORS = DummyCounter()

PII_PATTERNS = [re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), re.compile(r"\b\d{16}\b")]

def _redact(d: Any):
    s = json.dumps(d, default=str)
    for pat in PII_PATTERNS:
        s = pat.sub("[REDACTED]", s)
    return json.loads(s)

def guard(op_name: str):
    def deco(fn: Callable[..., Awaitable[Dict]]):
        @wraps(fn)
        async def wrapped(*args, **kwargs):
            try:
                res = await fn(*args, **kwargs)
                return _redact(res)
            except Exception as e:
                ERRORS.labels(component=op_name, error_type=type(e).__name__).inc()
                raise
        return wrapped
    return deco
