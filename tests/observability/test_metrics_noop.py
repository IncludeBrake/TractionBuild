from src.tractionbuild.observability.metrics import record_llm_metrics

def test_metrics_noop_without_backends():
    # Should not raise even if prometheus/opentelemetry are absent
    record_llm_metrics("dummy", 12.3, 10, 2)
