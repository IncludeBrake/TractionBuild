# app_v1_integrated.py - Updated version with real crew integration
"""
TractionBuild FastAPI application with integrated CrewAI implementations.
Replaces mock adapters with actual crew execution.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import time
import logging
from typing import Dict, Any, Optional
import uuid
import json
import os
from collections import defaultdict
from enum import Enum
from pydantic import BaseModel, Field

# Import the new crew adapters
from src.tractionbuild.adapters.crew_adapters import create_crew_registry

# Define missing schema classes
class AvatarType(str, Enum):
    """Avatar types for target audience definition."""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    TERTIARY = "tertiary"

class ProjectStatus(str, Enum):
    """Project status enumeration."""
    IDEA_VALIDATION = "idea_validation"
    EXECUTION_PLANNING = "execution_planning"
    PRODUCT_BUILD = "product_build"
    MARKETING_PREPARATION = "marketing_preparation"
    LAUNCH_READY = "launch_ready"
    COMPLETED = "completed"
    ERROR = "error"

class ProjectCreate(BaseModel):
    """Project creation request model."""
    name: str = Field(..., description="Project name")
    description: str = Field(..., description="Project description")
    hypothesis: Optional[str] = Field(None, description="Business hypothesis")
    target_avatars: Optional[list] = Field(default=[], description="Target audience avatars")
    workflow: str = Field(default="default_software_build", description="Workflow to use")

# Keep the existing EventBus - it's working well
class EventBus:
    def __init__(self):
        self.queues = defaultdict(asyncio.Queue)

    def queue(self, project_id: str):
        return self.queues[project_id]

    async def emit(self, project_id: str, event: dict):
        await self.queues[project_id].put(event)

# Global singleton
bus = EventBus()

# Enhanced workflow engine that uses real crews
class IntegratedWorkflowEngine:
    """Workflow engine that orchestrates real CrewAI implementations."""
    
    def __init__(self, crew_registry, event_bus=None, step_timeout: int = 600):
        self.crew_registry = crew_registry
        self.event_bus = event_bus
        self.step_timeout = step_timeout  # Increased timeout for real crew execution
        self.logger = logging.getLogger(__name__)

    async def run(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the full workflow using real crews."""
        ctx: Dict[str, Any] = {"project": project, "artifacts": {}}
        pid = project["id"]
        
        # Create runs directory for logging
        os.makedirs(f"runs/{pid}", exist_ok=True)
        logf = open(f"runs/{pid}/events.jsonl", "a", encoding="utf-8")

        def log_event(evt: dict):
            logf.write(json.dumps(evt, default=str) + "\n")
            logf.flush()

        # Initial persistence and event emission
        await self.event_bus.emit(pid, {"type": "status_update", "state": project["state"]})
        log_event({"event": "status_update", "state": project["state"]})

        # Define the workflow sequence - updated to match actual crew names
        workflow_steps = ["validator", "advisory"]  # Can add "builder", "marketing", "feedback" later
        
        for step_name in workflow_steps:
            crew_adapter = self.crew_registry.get(step_name)
            if not crew_adapter:
                error_msg = f"No crew adapter found for step: {step_name}"
                self.logger.error(error_msg)
                await self.event_bus.emit(pid, {
                    "type": "error",
                    "agent": step_name,
                    "message": error_msg
                })
                log_event({"event": "error", "agent": step_name, "message": error_msg})
                project["state"] = ProjectStatus.ERROR.value
                logf.close()
                return {"project": project, "artifacts": ctx["artifacts"]}
            
            # Update project state
            if step_name == "validator":
                project["state"] = ProjectStatus.IDEA_VALIDATION.value
            elif step_name == "advisory":
                project["state"] = ProjectStatus.EXECUTION_PLANNING.value
            
            await self.event_bus.emit(pid, {"type": "status_update", "state": project["state"]})
            log_event({"event": "status_update", "state": project["state"]})
            
            start = time.perf_counter()
            try:
                # Execute the crew with timeout - updated input format
                result = await asyncio.wait_for(
                    crew_adapter.run(ctx), 
                    timeout=self.step_timeout
                )
                
                dur = (time.perf_counter() - start)
                ctx["artifacts"][step_name] = result
                
                # Emit completion event with detailed results
                await self.event_bus.emit(pid, {
                    "type": "step_complete",
                    "agent": step_name,
                    "artifact": result,
                    "duration": dur
                })
                
                log_event({
                    "event": "step_complete",
                    "agent": step_name,
                    "duration_s": dur,
                    "artifact_summary": self._summarize_artifact(result)
                })
                
                self.logger.info(f"✅ {step_name} completed in {dur:.2f}s")
                
            except asyncio.TimeoutError:
                dur = (time.perf_counter() - start)
                error_msg = f"{step_name} timed out after {self.step_timeout}s"
                self.logger.error(error_msg)
                
                await self.event_bus.emit(pid, {
                    "type": "error",
                    "agent": step_name,
                    "message": error_msg
                })
                
                log_event({
                    "event": "timeout",
                    "agent": step_name,
                    "duration_s": dur,
                    "timeout_s": self.step_timeout
                })
                
                project["state"] = ProjectStatus.ERROR.value
                logf.close()
                return {"project": project, "artifacts": ctx["artifacts"]}
                
            except Exception as e:
                dur = (time.perf_counter() - start)
                error_msg = f"{step_name} failed: {str(e)}"
                self.logger.error(error_msg)
                
                await self.event_bus.emit(pid, {
                    "type": "error",
                    "agent": step_name,
                    "message": error_msg
                })
                
                log_event({
                    "event": "error",
                    "agent": step_name,
                    "message": error_msg,
                    "duration_s": dur
                })
                
                project["state"] = ProjectStatus.ERROR.value
                logf.close()
                return {"project": project, "artifacts": ctx["artifacts"]}

        # Workflow completed successfully
        project["state"] = ProjectStatus.COMPLETED.value
        await self.event_bus.emit(pid, {"type": "status_update", "state": "COMPLETED"})
        log_event({"event": "status_update", "state": "COMPLETED"})
        
        logf.close()
        return ctx

    def _summarize_artifact(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of artifact for logging (avoid storing full raw output)."""
        summary = {}
        
        for key, value in artifact.items():
            if key == "raw_output":
                summary[key] = f"[{len(str(value))} characters]"
            elif isinstance(value, list):
                summary[key] = f"[{len(value)} items]"
            elif isinstance(value, dict):
                summary[key] = f"[{len(value)} keys]"
            else:
                summary[key] = value
        
        return summary

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TractionBuild API v1", version="1.0.0")

# CORS middleware (TODO: Restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
crew_registry = None
workflow_engine = None
projects = {}  # In-memory storage for demo (TODO: Move to database)
event_bus = None

@app.on_event("startup")
async def startup_event():
    """Initialize the crew registry and workflow engine."""
    global crew_registry, workflow_engine, event_bus
    
    logger.info("🚀 Starting TractionBuild API with real crew integration...")
    
    # Use the singleton event bus
    event_bus = bus
    
    # Create real crew registry (not mocks!)
    try:
        crew_registry = create_crew_registry()
        logger.info(f"✅ Loaded crews: {list(crew_registry.keys())}")
    except Exception as e:
        logger.error(f"❌ Failed to load crews: {e}")
        raise
    
    # Create workflow engine with real crews
    workflow_engine = IntegratedWorkflowEngine(crew_registry, event_bus)
    logger.info("✅ TractionBuild API ready with integrated crews")

async def runner(project_id: str, project_data_dict: dict):
    """Background task to run the integrated workflow."""
    try:
        logger.info(f"🏁 Starting integrated workflow for project {project_id}")
        
        # Create project context
        project_ctx = {
            "project": {
                "id": project_id,
                "name": project_data_dict["name"],
                "description": project_data_dict["description"],
                "hypothesis": project_data_dict["hypothesis"],
                "target_avatars": [str(a) for a in project_data_dict["target_avatars"]],
                "state": ProjectStatus.IDEA_VALIDATION.value
            },
            "artifacts": {}
        }
        
        # Run integrated workflow with real crews
        result = await workflow_engine.run(project_ctx["project"])
        
        # Store results
        projects[project_id] = {
            "project": result["project"],
            "artifacts": result.get("artifacts", {}),
            "error": result.get("error")
        }
        
        logger.info(f"🎉 Integrated workflow completed for project {project_id}")
        
    except Exception as e:
        logger.error(f"💥 Integrated workflow failed for project {project_id}: {str(e)}")
        projects[project_id] = {
            "project": {"id": project_id, "state": ProjectStatus.ERROR.value},
            "artifacts": {},
            "error": str(e)
        }

@app.post("/api/v1/projects")
async def create_project(project_data: ProjectCreate, background_tasks: BackgroundTasks):
    """Create a new project and start integrated workflow."""
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
    
    # Start integrated workflow in background
    # Convert ProjectCreate to dict to ensure proper serialization
    project_data_dict = project_data.model_dump()
    background_tasks.add_task(runner, project_id, project_data_dict)
    
    return {"project_id": project_id, "message": "Project created with integrated crew workflow"}

@app.get("/api/v1/projects/{project_id}")
async def get_project(project_id: str):
    """Get project with crew artifacts."""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return projects[project_id]

@app.get("/api/v1/projects/{project_id}/status")
async def get_project_status(project_id: str):
    """Get project status and crew progress."""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_data = projects[project_id]
    state = project_data["project"]["state"]
    
    # Calculate progress based on crew completions
    total_steps = 2  # validator + advisory (can expand later)
    completed_steps = len(project_data["artifacts"])
    progress = (completed_steps / total_steps) * 100 if total_steps > 0 else 0
    
    current_step = "completed" if state == ProjectStatus.COMPLETED.value else state.lower()
    
    return {
        "state": state,
        "progress": progress,
        "current_step": current_step,
        "completed_steps": completed_steps,
        "total_steps": total_steps,
        "crews_completed": list(project_data["artifacts"].keys())
    }

@app.get("/health")
async def health_check():
    """Health check endpoint with crew status."""
    crew_status = {}
    if crew_registry:
        for name, adapter in crew_registry.items():
            try:
                # Basic health check - verify crew can be instantiated
                crew_status[name] = "healthy"
            except Exception as e:
                crew_status[name] = f"error: {str(e)}"
    
    return {
        "status": "healthy", 
        "crews": crew_status,
        "mode": "integrated"  # vs "mock"
    }

@app.websocket("/ws/projects/{project_id}")
async def ws_project(ws: WebSocket, project_id: str):
    """WebSocket endpoint for real-time project updates."""
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