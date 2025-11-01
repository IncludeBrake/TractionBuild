import json, logging, sys, time, re
from typing import Any, Mapping
from src.tractionbuild.core.settings import get_settings

_PII_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), # SSN-like
    re.compile(r"\b(?:\d[ -]*?){13,16}\b"), # card-ish
    re.compile(r"\b[A-Za-z0-9._%+-]+ @[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
]

def _redact(v: str) -> str:
    s = v
    for pat in _PII_PATTERNS:
        s = pat.sub("[REDACTED]", s)
    return s

class JsonLogFormatter(logging.Formatter):
    def format(self, record):
        s = get_settings()
        payload: dict[str, Any] = {
            "ts": time.time(),
            "level": record.levelname,
            "msg": record.getMessage(),
            "logger": record.name,
            "env": s.ENV,
        }
        if isinstance(record.args, Mapping):
            extra = {k: ( _redact(str(v)) if (not s.LOG_PII and isinstance(v,str)) else v)
                     for k,v in record.args.items()}
            payload.update(extra)
        return json.dumps(payload, ensure_ascii=False)

def configure_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLogFormatter())
    root = logging.getLogger()
    root.setLevel(get_settings().LOG_LEVEL)
    root.handlers[:] = [handler]