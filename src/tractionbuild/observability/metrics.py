from __future__ import annotations
from typing import Any

# Prometheus client (optional)
try:
    from prometheus_client import Counter, Histogram
    PROM= True
except Exception:
    PROM= False
    Counter = Histogram = None  # type: ignore

# OpenTelemetry (optional)
try:
    from opentelemetry import trace
    from opentelemetry.metrics import get_meter
    OTEL= True
    _tracer = trace.get_tracer("tractionbuild")
    _meter  = get_meter("tractionbuild")
except Exception:
    OTEL= False
    _tracer = None
    _meter  = None

if PROM:
    LLM_CALLS = Counter("tb_llm_calls_total", "Total LLM calls", ["model"])
    LLM_LAT   = Histogram("tb_llm_latency_ms", "LLM latency (ms)", ["model"])
else:
    LLM_CALLS = LLM_LAT = None  # type: ignore

def record_llm_metrics(model: str, latency_ms: float, prompt_tokens: int, completion_tokens: int) -> None:
    # Prometheus
    if PROM and LLM_CALLS and LLM_LAT:
        LLM_CALLS.labels(model=model).inc()
        LLM_LAT.labels(model=model).observe(latency_ms)

    # OpenTelemetry (span-only if no SDK/exporter configured)
    if OTEL and _tracer:
        with _tracer.start_as_current_span("tb.llm.call") as span:  # type: ignore
            span.set_attribute("model", model)
            span.set_attribute("latency_ms", float(latency_ms))
            span.set_attribute("prompt_tokens", int(prompt_tokens))
            span.set_attribute("completion_tokens", int(completion_tokens))
