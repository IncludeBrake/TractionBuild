from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer("tractionbuild")

def trace_operation(operation: str, **attributes):
    with tracer.start_as_current_span(operation) as span:
        for k, v in attributes.items():
            span.set_attribute(k, v)
