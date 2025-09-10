from fastapi import APIRouter, HTTPException
from src.smm.pipeline import SMM
from src.core.types import CrewResult
from src.services.project_registry import ProjectRegistry
from src.observability.metrics import request_count
from uuid import uuid4
from typing import Dict, Any

router = APIRouter(prefix="/ideas")

@router.post("/ingest")
async def ingest_idea(idea: Dict[str, Any]):
    """Ingest a new idea and trigger SMM analysis."""
    # Track API usage
    request_count.labels(endpoint="/ideas/ingest", method="POST").inc()

    # Validate input
    idea_text = idea.get("text", "").strip()
    if not idea_text:
        raise HTTPException(status_code=400, detail="Missing or empty idea_text")

    if len(idea_text) < 10:
        raise HTTPException(status_code=400, detail="Idea text too short (minimum 10 characters)")

    if len(idea_text) > 1000:
        raise HTTPException(status_code=400, detail="Idea text too long (maximum 1000 characters)")

    try:
        # Generate project ID
        project_id = str(uuid4())

        # Initialize registry and create project
        registry = ProjectRegistry()
        registry.create_project(project_id, idea_text)

        # Run SMM analysis
        smm = SMM()
        result = smm.run(project_id, idea_text)

        # Store results in registry
        registry.append_crew_result(project_id, result)

        # Return success response
        return {
            "project_id": project_id,
            "status": "success",
            "message": "Idea ingested and analyzed successfully",
            "smm_summary": result.summary,
            "artifacts_count": len(result.artifacts),
            "cache_hit": result.stats.get("cache_hit", False)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process idea: {str(e)}")

@router.get("/status/{project_id}")
async def get_smm_status(project_id: str):
    """Get SMM analysis status for a project."""
    try:
        registry = ProjectRegistry()
        project_data = registry.get_project_data(project_id)

        if not project_data:
            raise HTTPException(status_code=404, detail="Project not found")

        smm_results = registry.get_crew_results(project_id, "SMM")

        if not smm_results:
            return {
                "project_id": project_id,
                "status": "pending",
                "message": "SMM analysis not yet completed"
            }

        # Get the latest SMM result
        latest_result = smm_results[0]  # Results are ordered by timestamp

        return {
            "project_id": project_id,
            "status": "completed",
            "smm_ok": latest_result.get("ok", False),
            "summary": latest_result.get("summary", ""),
            "artifacts_count": len(latest_result.get("artifact_paths", [])),
            "stats": latest_result.get("stats", {}),
            "timestamp": latest_result.get("timestamp", "")
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")
