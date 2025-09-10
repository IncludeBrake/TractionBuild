from prometheus_client import Counter, Gauge, Histogram

request_count = Counter("http_requests_total", "Total HTTP Requests", ["endpoint", "method"])
token_usage = Gauge("llm_token_usage", "LLM Token Usage", ["model", "crew_name"])
latency = Histogram("operation_latency_ms", "Operation Latency", ["operation", "crew_name"])

def log_tokens(model: str, crew_name: str, tokens_in: int, tokens_out: int):
    token_usage.labels(model=model, crew_name=crew_name).set(tokens_in + tokens_out)
    latency.labels(operation="llm_call", crew_name=crew_name).observe(tokens_in + tokens_out)
