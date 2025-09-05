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

# Standalone EventBus implementation
class EventBus:
    def __init__(self):
        self.queues = defaultdict(asyncio.Queue)

    def queue(self, project_id: str):
        return self.queues[project_id]

    async def emit(self, project_id: str, event: dict):
        await self.queues[project_id].put(event)

# Global singleton
bus = EventBus()

# Mock schemas for standalone version
from enum import Enum
from pydantic import BaseModel, Field
from typing import List

class AvatarType(str, Enum):
    STARTUP = "startup_entrepreneur"
    SME = "sme"
    INVESTOR = "investor_incubator"
    CORP_LAB = "corporate_innovation_lab"

class ProjectStatus(str, Enum):
    IDEA_VALIDATION = "IDEA_VALIDATION"
    EXECUTION_PLANNING = "EXECUTION_PLANNING"
    BUILD_PHASE = "BUILD_PHASE"
    MARKETING_LAUNCH = "MARKETING_LAUNCH"
    QUALITY_ASSURANCE = "QUALITY_ASSURANCE"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"

class ProjectCreate(BaseModel):
    name: str
    description: str
    hypothesis: str
    target_avatars: List[AvatarType] = Field(min_items=1)
    workflow: str = "validation_and_launch"

# Mock crew adapters with security guards
from functools import wraps
import time

def guard(op_name: str):
    def deco(fn):
        @wraps(fn)
        async def wrapped(*args, **kwargs):
            try:
                res = await fn(*args, **kwargs)
                return res
            except Exception as e:
                # Log error (in production, this would use Prometheus metrics)
                print(f"ERROR in {op_name}: {e}")
                raise
        return wrapped
    return deco

class MockValidatorAdapter:
    @guard("validator.execute")
    async def run(self, project_ctx):
        await asyncio.sleep(2)  # Simulate work
        return {
            "go_recommendation": True,
            "confidence": 0.85,
            "avatars": [],
            "mvp_features": ["feature1", "feature2"],
            "risks": ["risk1"],
            "findings": []
        }

class MockAdvisoryAdapter:
    @guard("advisory.execute")
    async def run(self, project_ctx):
        await asyncio.sleep(2)  # Simulate work
        return {
            "approved": True,
            "rationale": "Good idea",
            "must_haves": ["must1"],
            "cut_scope": [],
            "kpis": {"revenue": 100000}
        }

# Production workflow engine with metrics, persistence, and logging
class MockWorkflowEngine:
    def __init__(self, registry, event_bus=None, step_timeout: int = 300):
        self.registry = registry
        self.event_bus = event_bus
        self.step_timeout = step_timeout

    async def run(self, project: Dict[str, Any]) -> Dict[str, Any]:
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

        for key in ["validator", "advisory"]:
            agent = self.registry.get(key)
            start = time.perf_counter()
            try:
                res = await asyncio.wait_for(agent.run(ctx), timeout=self.step_timeout)
                dur = (time.perf_counter() - start)
                ctx["artifacts"][key] = res
                
                # Emit completion event
                await self.event_bus.emit(pid, {
                    "type": "step_complete",
                    "agent": key,
                    "artifact": res
                })
                log_event({
                    "event": "step_complete",
                    "agent": key,
                    "duration_s": dur,
                    "artifact_type": key
                })
                
            except Exception as e:
                dur = (time.perf_counter() - start)
                await self.event_bus.emit(pid, {
                    "type": "error",
                    "agent": key,
                    "message": str(e)
                })
                log_event({
                    "event": "error",
                    "agent": key,
                    "message": str(e)
                })
                project["state"] = ProjectStatus.ERROR.value
                logf.close()
                return {"project": project, "artifacts": ctx["artifacts"]}

        project["state"] = ProjectStatus.COMPLETED.value
        await self.event_bus.emit(pid, {"type": "status_update", "state": "COMPLETED"})
        log_event({"event": "status_update", "state": "COMPLETED"})
        logf.close()
        return ctx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="tractionbuild API v1", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
agent_registry = None
workflow_engine = None
projects = {}  # In-memory storage for demo
event_bus = None

@app.on_event("startup")
async def startup_event():
    """Initialize the agent registry and workflow engine."""
    global agent_registry, workflow_engine, event_bus
    
    # Use the singleton event bus
    event_bus = bus
    
    # Create mock registry
    agent_registry = {
        "validator": MockValidatorAdapter(),
        "advisory": MockAdvisoryAdapter()
    }
    workflow_engine = MockWorkflowEngine(agent_registry, event_bus)

async def runner(project_id: str, project_data_dict: dict):
    """Background task to run the workflow."""
    try:
        # Create project context
        project_ctx = {
            "project": {
                "id": project_id,
                "name": project_data_dict["name"],
                "description": project_data_dict["description"],
                "hypothesis": project_data_dict["hypothesis"],
                "target_avatars": [a for a in project_data_dict["target_avatars"]],
                "state": ProjectStatus.IDEA_VALIDATION.value
            },
            "artifacts": {}
        }
        
        # Run workflow
        result = await workflow_engine.run(project_ctx["project"])
        
        # Store results
        projects[project_id] = {
            "project": result["project"],
            "artifacts": result.get("artifacts", {}),
            "error": result.get("error")
        }
        
        logger.info(f"Workflow completed for project {project_id}")
        
    except Exception as e:
        logger.error(f"Workflow failed for project {project_id}: {str(e)}")
        projects[project_id] = {
            "project": {"id": project_id, "state": ProjectStatus.ERROR.value},
            "artifacts": {},
            "error": str(e)
        }

@app.post("/api/v1/projects")
async def create_project(project_data: ProjectCreate, background_tasks: BackgroundTasks):
    """Create a new project and start background workflow."""
    project_id = str(uuid.uuid4())
    
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
    
    # Start background workflow
    # Convert ProjectCreate to dict to ensure proper serialization
    project_data_dict = project_data.model_dump()
    background_tasks.add_task(runner, project_id, project_data_dict)
    
    return {"project_id": project_id}

@app.get("/api/v1/projects/{project_id}")
async def get_project(project_id: str):
    """Get project with artifacts."""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return projects[project_id]

@app.get("/api/v1/projects/{project_id}/status")
async def get_project_status(project_id: str):
    """Get project status and progress."""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_data = projects[project_id]
    state = project_data["project"]["state"]
    
    # Calculate progress
    total_steps = 2  # validator + advisory
    completed_steps = len(project_data["artifacts"])
    progress = (completed_steps / total_steps) * 100 if total_steps > 0 else 0
    
    current_step = "completed" if state == ProjectStatus.COMPLETED.value else "running"
    
    return {
        "state": state,
        "progress": progress,
        "current_step": current_step,
        "completed_steps": completed_steps,
        "total_steps": total_steps
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "agents": list(agent_registry.keys()) if agent_registry else []}

@app.websocket("/ws/projects/{project_id}")
async def ws_project(ws: WebSocket, project_id: str):
    """WebSocket endpoint for real-time project updates."""
    await ws.accept()
    q = event_bus.queue(project_id)
    try:
        while True:
            event = await q.get()
            await ws.send_json(event)
    except WebSocketDisconnect:
        return
