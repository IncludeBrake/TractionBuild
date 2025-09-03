# app_v1_real_integration.py - Use your actual CrewController system
"""
TractionBuild FastAPI application integrated with your actual CrewController.
This replaces the mock workflow engine with your sophisticated production system.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import time
import logging
from typing import Dict, Any
import uuid
import json
import os
from collections import defaultdict

# Import your actual sophisticated components
from src.tractionbuild.core.crew_controller import CrewController
from src.tractionbuild.database.project_registry import ProjectRegistry
from src.tractionbuild.core.schemas import ProjectStatus, ProjectCreate

# Keep the existing EventBus - it's working
class EventBus:
    def __init__(self):
        self.queues = defaultdict(asyncio.Queue)

    def queue(self, project_id: str):
        return self.queues[project_id]

    async def emit(self, project_id: str, event: dict):
        await self.queues[project_id].put(event)

# Global singleton
bus = EventBus()

# Real workflow engine using your CrewController
class CrewControllerWorkflowEngine:
    """Workflow engine that uses your sophisticated CrewController system."""
    
    def __init__(self, project_registry: ProjectRegistry = None, event_bus: EventBus = None):
        self.project_registry = project_registry
        self.event_bus = event_bus
        
    async def run(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow using CrewController."""
        pid = project["id"]
        
        # Create runs directory for logging
        os.makedirs(f"runs/{pid}", exist_ok=True)
        logf = open(f"runs/{pid}/events.jsonl", "a", encoding="utf-8")

        def log_event(evt: dict):
            logf.write(json.dumps(evt, default=str) + "\n")
            logf.flush()

        # Initial event
        await self.event_bus.emit(pid, {"type": "status_update", "state": project["state"]})
        log_event({"event": "workflow_started", "project_id": pid, "initial_state": project["state"]})

        try:
            # Initialize CrewController with your sophisticated system
            controller = CrewController(project)
            
            # Set registry if available
            if self.project_registry:
                controller.set_registry(self.project_registry)
            
            # Execute using your advanced routing and execution
            start_time = time.perf_counter()
            result = await controller.route_and_execute()
            duration = time.perf_counter() - start_time
            
            # Emit completion event
            await self.event_bus.emit(pid, {
                "type": "crew_controller_complete", 
                "duration": duration,
                "final_state": result.get("state"),
                "execution_summary": controller.get_execution_summary()
            })
            
            log_event({
                "event": "crew_controller_complete",
                "duration_s": duration,
                "final_state": result.get("state"),
                "iterations": controller.iteration_count
            })
            
            logf.close()
            return {"project": result, "artifacts": result.get("artifacts", {})}
            
        except Exception as e:
            error_msg = f"CrewController execution failed: {str(e)}"
            logging.error(error_msg)
            
            await self.event_bus.emit(pid, {
                "type": "error",
                "message": error_msg
            })
            
            log_event({
                "event": "error",
                "message": error_msg
            })
            
            logf.close()
            project["state"] = ProjectStatus.ERROR.value
            return {"project": project, "artifacts": {}}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TractionBuild API v1 - Real Integration", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
project_registry = None
workflow_engine = None
projects = {}  # In-memory storage for demo
event_bus = None

@app.on_event("startup")
async def startup_event():
    """Initialize the real CrewController system."""
    global project_registry, workflow_engine, event_bus
    
    logger.info("🚀 Starting TractionBuild API with CrewController integration...")
    
    # Use the singleton event bus
    event_bus = bus
    
    try:
        # Initialize Neo4j project registry with connection details
        try:
            # Try different parameter combinations based on your ProjectRegistry implementation
            project_registry = ProjectRegistry(
                neo4j_uri="bolt://localhost:7687",
                neo4j_user="neo4j"
            )
            await project_registry.__aenter__()
            logger.info("✅ Neo4j ProjectRegistry initialized and connected")
        except Exception as e:
            logger.warning(f"⚠️ Neo4j ProjectRegistry failed (continuing without): {e}")
            project_registry = None
        
        # Create workflow engine with CrewController
        workflow_engine = CrewControllerWorkflowEngine(project_registry, event_bus)
        
        logger.info("✅ TractionBuild API ready with CrewController integration")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize CrewController system: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown of resources."""
    global project_registry
    
    if project_registry:
        try:
            await project_registry.__aexit__(None, None, None)
            logger.info("✅ ProjectRegistry closed cleanly")
        except Exception as e:
            logger.error(f"Error closing ProjectRegistry: {e}")

async def runner(project_id: str, project_data: ProjectCreate):
    """Background task to run CrewController workflow."""
    try:
        logger.info(f"🏁 Starting CrewController workflow for project {project_id}")
        
        # Create project context for CrewController
        project_ctx = {
            "id": project_id,
            "name": project_data.name,
            "description": project_data.description,
            "hypothesis": project_data.hypothesis,
            "target_avatars": [str(a) for a in project_data.target_avatars],
            "workflow": project_data.workflow,
            "state": ProjectStatus.IDEA_VALIDATION.value,
            "idea": f"{project_data.name}: {project_data.description}. Hypothesis: {project_data.hypothesis}"
        }
        
        # Run CrewController workflow
        result = await workflow_engine.run(project_ctx)
        
        # Store results
        projects[project_id] = {
            "project": result["project"],
            "artifacts": result.get("artifacts", {}),
            "error": result.get("error")
        }
        
        logger.info(f"🎉 CrewController workflow completed for project {project_id}")
        
    except Exception as e:
        logger.error(f"💥 CrewController workflow failed for project {project_id}: {str(e)}")
        projects[project_id] = {
            "project": {"id": project_id, "state": ProjectStatus.ERROR.value},
            "artifacts": {},
            "error": str(e)
        }

@app.post("/api/v1/projects")
async def create_project(project_data: ProjectCreate, background_tasks: BackgroundTasks):
    """Create a new project and start CrewController workflow."""
    project_id = str(uuid.uuid4())
    
    logger.info(f"📋 Creating project {project_id}: {project_data.name}")
    
    # Store initial project
    projects[project_id] = {
        "project": {
            "id": project_id,
            "name": project_data.name,
            "description": project_data.description,
            "state": ProjectStatus.IDEA_VALIDATION.value
        },
        "artifacts": {},
        "error": None
    }
    
    # Start CrewController workflow in background
    background_tasks.add_task(runner, project_id, project_data)
    
    return {
        "project_id": project_id, 
        "message": "Project created with CrewController workflow",
        "system": "CrewController with advanced loop prevention"
    }

@app.get("/api/v1/projects/{project_id}")
async def get_project(project_id: str):
    """Get project with CrewController artifacts."""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return projects[project_id]

@app.get("/api/v1/projects/{project_id}/status")
async def get_project_status(project_id: str):
    """Get project status from CrewController."""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_data = projects[project_id]
    state = project_data["project"]["state"]
    
    # More sophisticated progress calculation based on CrewController states
    progress = 0
    if state == ProjectStatus.IDEA_VALIDATION.value:
        progress = 20
    elif state == "IN_PROGRESS":
        progress = 60
    elif state == ProjectStatus.COMPLETED.value:
        progress = 100
    elif state == ProjectStatus.ERROR.value:
        progress = 0
    
    return {
        "state": state,
        "progress": progress,
        "current_step": state.lower(),
        "artifacts_count": len(project_data["artifacts"]),
        "system": "CrewController",
        "has_error": project_data.get("error") is not None
    }

@app.get("/health")
async def health_check():
    """Health check with CrewController system status."""
    health_info = {
        "status": "healthy",
        "system": "CrewController",
        "mode": "production"
    }
    
    # Check ProjectRegistry
    if project_registry:
        health_info["database"] = "neo4j_connected"
    else:
        health_info["database"] = "neo4j_disabled"
    
    # Check if we can import key components
    try:
        from src.tractionbuild.crews import CREW_REGISTRY
        health_info["crews"] = list(CREW_REGISTRY.keys())
    except Exception as e:
        health_info["crews"] = f"error: {str(e)}"
    
    return health_info

@app.websocket("/ws/projects/{project_id}")
async def ws_project(ws: WebSocket, project_id: str):
    """WebSocket endpoint for real-time CrewController updates."""
    await ws.accept()
    q = event_bus.queue(project_id)
    try:
        logger.info(f"🔌 WebSocket connected for project {project_id}")
        while True:
            event = await q.get()
            await ws.send_json(event)
    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected for project {project_id}")
        return

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)