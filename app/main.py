from fastapi import FastAPI, Response
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from app.routers.ideas import router as ideas_router

app = FastAPI(title="TractionBuild API", version="1.0.0")
FastAPIInstrumentor.instrument_app(app)

# Include routers
app.include_router(ideas_router)

@app.get("/metrics")
async def metrics():
    from prometheus_client import generate_latest
    return Response(generate_latest(), media_type="text/plain")

@app.get("/")
async def root():
    return {"message": "TractionBuild API", "status": "healthy"}
