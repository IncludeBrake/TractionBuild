import asyncio
import logging
import uuid
from typing import Dict, Any

from fastapi import FastAPI, BackgroundTasks, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# --- Corrected Imports with 'tractionbuild' package name ---
# Fixed with relative imports
from ..main import tractionbuildOrchestrator
from ..core.schemas import ProjectCreate, ProjectStatus
from .events import bus

# --- App Initialization ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="tractionbuild Production API",
    version="2.0.0",
    description="Unified API for the tractionbuild AI-powered product development platform."
)

projects: Dict[str, Dict[str, Any]] = {}

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Background Workflow Runner ---
async def workflow_runner(project_id: str, project_data: ProjectCreate):
    logger.info(f"Starting workflow for project_id: {project_id}")
    try:
        async with tractionbuildOrchestrator() as orchestrator:
            initial_project_context = await orchestrator.create_project(
                idea=project_data.description,
                workflow_name=project_data.workflow
            )
            initial_project_context['id'] = project_id
            projects[project_id] = initial_project_context

            final_project_context = await orchestrator.execute_workflow(initial_project_context)
            projects[project_id] = final_project_context
            
            await bus.emit(project_id, {"type": "status_update", "state": final_project_context.get('state', 'COMPLETED')})

    except Exception as e:
        logger.error(f"Workflow for project {project_id} failed: {e}", exc_info=True)
        error_state = {
            "id": project_id,
            "state": ProjectStatus.ERROR.value,
            "error": str(e)
        }
        projects[project_id] = error_state
        await bus.emit(project_id, {"type": "error", "message": str(e)})

# --- API Endpoints (No changes needed here) ---
@app.post("/api/v1/projects", status_code=202)
async def create_project(project_data: ProjectCreate, background_tasks: BackgroundTasks):
    project_id = str(uuid.uuid4())
    projects[project_id] = { "id": project_id, "name": project_data.name, "state": ProjectStatus.IDEA_VALIDATION.value }
    background_tasks.add_task(workflow_runner, project_id, project_data)
    return {"project_id": project_id, "status_url": f"/api/v1/projects/{project_id}/status"}

@app.get("/api/v1/projects/{project_id}/status")
async def get_project_status(project_id: str):
    # ... (rest of the file is the same)
    project = projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    state = project.get("state", "UNKNOWN")
    progress = 100 if state in [ProjectStatus.COMPLETED.value, ProjectStatus.ERROR.value] else 50
    return {"project_id": project_id, "state": state, "progress": progress}

@app.websocket("/ws/projects/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    # ... (rest of the file is the same)
    await websocket.accept()
    q = bus.queue(project_id)
    try:
        while True:
            event = await q.get()
            await websocket.send_json(event)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for project {project_id}")