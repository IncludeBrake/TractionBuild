"""
FastAPI application for ZeroToShip.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import redis
import json
import logging
from datetime import datetime

app = FastAPI(
    title="ZeroToShip API",
    description="AI-powered product studio API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "ZeroToShip API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ZeroToShip API"}


@app.get("/projects")
async def get_projects():
    """Get all projects."""
    # Placeholder implementation
    return {"projects": []}


@app.post("/projects")
async def create_project(project_data: Dict[str, Any]):
    """Create a new project."""
    # Placeholder implementation
    return {"project_id": "project_1", "status": "created"}


@app.get("/projects/{project_id}")
async def get_project(project_id: str):
    """Get a specific project."""
    # Placeholder implementation
    return {"project_id": project_id, "status": "found"}


# Initialize Redis client for observability data
redis_client = redis.Redis(host='localhost', port=6379, db=0)


@app.get("/dashboard/metrics")
async def get_dashboard_metrics():
    """Get real-time dashboard metrics."""
    try:
        # Get current metrics from Redis
        metrics_data = redis_client.get("metrics:current")
        if metrics_data:
            metrics = json.loads(metrics_data)
        else:
            # Return default metrics if none available
            metrics = {
                "quality_score": 0.85,
                "cost_per_1k_tokens": 0.002,
                "drift_score": 0.05,
                "time_to_value": 120.0,
                "error_rate": 0.03,
                "carbon_footprint": 0.5,
                "compliance_score": 0.95
            }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics
        }
    except Exception as e:
        logging.error(f"Error getting dashboard metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics")


@app.get("/dashboard/anomalies")
async def get_dashboard_anomalies():
    """Get current anomalies and alerts."""
    try:
        # Get observability data from Redis
        observability_data = redis_client.get("observability:current")
        if observability_data:
            data = json.loads(observability_data)
            anomalies = data.get("anomalies", [])
        else:
            anomalies = []
        
        return {
            "timestamp": datetime.now().isoformat(),
            "anomalies": anomalies,
            "total_anomalies": len(anomalies)
        }
    except Exception as e:
        logging.error(f"Error getting anomalies: {e}")
        raise HTTPException(status_code=500, detail="Failed to get anomalies")


@app.get("/dashboard/recommendations")
async def get_dashboard_recommendations():
    """Get improvement recommendations."""
    try:
        # Get observability data from Redis
        observability_data = redis_client.get("observability:current")
        if observability_data:
            data = json.loads(observability_data)
            recommendations = data.get("recommendations", [])
        else:
            recommendations = []
        
        return {
            "timestamp": datetime.now().isoformat(),
            "recommendations": recommendations,
            "total_recommendations": len(recommendations)
        }
    except Exception as e:
        logging.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recommendations")


@app.post("/dashboard/run-observability")
async def run_observability_analysis(project_data: Dict[str, Any]):
    """Run observability analysis for a project."""
    try:
        from ..crews.observability_crew import ObservabilityCrew
        
        # Create observability crew
        crew = ObservabilityCrew(project_data)
        
        # Run analysis
        result = await crew.run_async(project_data)
        
        return {
            "status": "success",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logging.error(f"Error running observability analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to run analysis: {str(e)}")


@app.get("/dashboard/overview")
async def get_dashboard_overview():
    """Get comprehensive dashboard overview."""
    try:
        # Get all dashboard data
        metrics_data = redis_client.get("metrics:current")
        observability_data = redis_client.get("observability:current")
        
        metrics = json.loads(metrics_data) if metrics_data else {}
        observability = json.loads(observability_data) if observability_data else {}
        
        # Calculate overall health score
        health_score = 0.0
        if metrics:
            quality = metrics.get("quality_score", 0.8)
            error_rate = metrics.get("error_rate", 0.05)
            compliance = metrics.get("compliance_score", 0.95)
            
            health_score = (quality * 0.4 + (1 - error_rate) * 0.3 + compliance * 0.3)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "health_score": health_score,
            "metrics": metrics,
            "anomalies": observability.get("anomalies", []),
            "recommendations": observability.get("recommendations", []),
            "summary": {
                "total_anomalies": len(observability.get("anomalies", [])),
                "total_recommendations": len(observability.get("recommendations", [])),
                "system_status": "healthy" if health_score > 0.8 else "warning" if health_score > 0.6 else "critical"
            }
        }
    except Exception as e:
        logging.error(f"Error getting dashboard overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard overview") 