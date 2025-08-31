from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import time
import logging
import uuid
import json
import os
from typing import Dict, Any, List
from enum import Enum
from pydantic import BaseModel

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

# Simple enums for the minimal slice
class ProjectStatus(str, Enum):
    IDEA_VALIDATION = "idea_validation"
    ADVISORY_REVIEW = "advisory_review"
    COMPLETED = "completed"
    ERROR = "error"

class TargetAvatar(str, Enum):
    STARTUP_ENTREPRENEUR = "startup_entrepreneur"

# Simple schemas
class ProjectCreate(BaseModel):
    name: str
    description: str
    hypothesis: str
    target_avatars: List[str]
    workflow: str

# Global state
projects = {}  # In-memory storage for demo

def write_event(project_id: str, event_type: str, agent: str, artifact: Dict[str, Any]):
    """Write event to events.jsonl file."""
    try:
        # Ensure runs directory exists
        runs_dir = "runs"
        project_dir = os.path.join(runs_dir, project_id)
        os.makedirs(project_dir, exist_ok=True)
        
        event = {
            "timestamp": time.time(),
            "project_id": project_id,
            "type": event_type,
            "agent": agent,
            "artifact": artifact
        }
        
        events_file = os.path.join(project_dir, "events.jsonl")
        with open(events_file, "a") as f:
            f.write(json.dumps(event) + "\n")
            
        logger.info(f"Event written to {events_file}")
    except Exception as e:
        logger.error(f"Failed to write event: {e}")

async def mock_workflow_runner(project_id: str, project_data: ProjectCreate):
    """Mock workflow that simulates the validation and advisory process."""
    try:
        logger.info(f"Starting mock workflow for project {project_id}")
        
        # Step 1: Idea Validation (simulate 3 seconds)
        await asyncio.sleep(3)
        projects[project_id]["project"]["state"] = ProjectStatus.ADVISORY_REVIEW.value
        validator_artifact = {
            "go_recommendation": "GO",
            "confidence": 0.85,
            "reasoning": "Strong market validation and clear value proposition"
        }
        projects[project_id]["artifacts"]["validator"] = validator_artifact
        write_event(project_id, "step_complete", "validator", validator_artifact)
        logger.info(f"Validator completed for project {project_id}")
        
        # Step 2: Advisory Review (simulate 2 seconds)
        await asyncio.sleep(2)
        advisory_artifact = {
            "approved": True,
            "rationale": "Project meets all criteria for launch",
            "recommendations": ["Focus on MVP", "Start with beta users"]
        }
        projects[project_id]["artifacts"]["advisory"] = advisory_artifact
        write_event(project_id, "step_complete", "advisory", advisory_artifact)
        logger.info(f"Advisory completed for project {project_id}")
        
        # Step 3: Marketing (simulate 2 seconds)
        await asyncio.sleep(2)
        projects[project_id]["project"]["state"] = ProjectStatus.COMPLETED.value
        marketing_artifact = {
            "positioning": "AI product team for startup entrepreneurs",
            "landing_copy": "🚀 AI-powered automation for startup entrepreneurs who want achieve their goals faster",
            "twitter": [
                "🔥 Stop losing time and money to manual processes\n\n10x faster workflow\n\n#AI #Productivity",
                "🚀 startup entrepreneur alert!\n\nmanual processes → AI automation\n\nTry it free →"
            ],
            "linkedin": [
                "🎯 startup entrepreneurs are facing a critical challenge: inefficient workflows\n\nBut what if there was a AI-powered automation that could 10x productivity gains?\n\nThe future belongs to those who automate intelligently\n\nDM me to learn more"
            ],
            "email_seed": "Subject: Stop losing time and money to manual processes\n\nHi startup entrepreneurs,\n\nmanual processes is costing you hours every week.\n\nBut AI automation can focus on what matters.\n\nSchedule a demo\n\nBest,\nThe ZeroToShip Team",
            "youtube_script": "🎬 Stop losing time and money to manual processes\n\nIn this video, I'll show you how AI-powered automation is revolutionizing how teams work for startup entrepreneurs.\n\nWe'll cover: 1) The problem 2) The solution 3) Real results\n\nSubscribe for more AI insights"
        }
        projects[project_id]["artifacts"]["marketing"] = marketing_artifact
        write_event(project_id, "step_complete", "marketing", marketing_artifact)
        
        logger.info(f"Workflow completed for project {project_id}")
        
    except Exception as e:
        logger.error(f"Workflow failed for project {project_id}: {str(e)}")
        projects[project_id]["project"]["state"] = ProjectStatus.ERROR.value
        projects[project_id]["error"] = str(e)

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
            "hypothesis": project_data.hypothesis,
            "target_avatars": project_data.target_avatars,
            "state": ProjectStatus.IDEA_VALIDATION.value
        },
        "artifacts": {},
        "error": None
    }
    
    # Start background workflow
    background_tasks.add_task(mock_workflow_runner, project_id, project_data)
    
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
    total_steps = 3  # validator + advisory + marketing
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
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return {
        "projects_total": len(projects),
        "projects_completed": len([p for p in projects.values() if p["project"]["state"] == ProjectStatus.COMPLETED.value]),
        "projects_error": len([p for p in projects.values() if p["project"]["state"] == ProjectStatus.ERROR.value])
    }
