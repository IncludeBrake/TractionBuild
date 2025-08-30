from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import APIRouter, Response

AGENT_EXECUTIONS = Counter("zerotoship_agent_executions_total",
                           "Total agent executions", ["agent_name", "status"])
AGENT_DURATION = Histogram("zerotoship_agent_duration_seconds",
                           "Agent execution duration", ["agent_name"])
ERRORS = Counter("zerotoship_errors_total", "Total errors", ["component","error_type"])

router = APIRouter()

@router.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
