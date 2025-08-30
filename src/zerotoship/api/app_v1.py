from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import time
import logging
from typing import Dict, Any

from ..schemas import ProjectCreate, ProjectStatus
from ..core.workflow_engine import WorkflowEngine
from ..core.agent_registry import AgentRegistry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ZeroToShip API v1", version="1.0.0")

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

@app.on_event("startup")
async def startup_event():
    """Initialize the agent registry and workflow engine."""
    global agent_registry, workflow_engine
    
    agent_registry = AgentRegistry()
    workflow_engine = WorkflowEngine(agent_registry)

async def runner(project_id: str, project_data: ProjectCreate):
    """Background task to run the workflow."""
    try:
        # Create project context
        project_ctx = {
            "project": {
                "id": project_id,
                "name": project_data.name,
                "description": project_data.description,
                "hypothesis": project_data.hypothesis,
                "target_avatars": [a.value for a in project_data.target_avatars],
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
    import uuid
    
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
    background_tasks.add_task(runner, project_id, project_data)
    
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
    return {"status": "healthy", "agents": agent_registry.list_agents() if agent_registry else []}
