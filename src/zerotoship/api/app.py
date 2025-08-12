import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from celery.result import AsyncResult
from ..tasks.crew_tasks import execute_workflow_task # Import the task from the new file
import uuid

logger = logging.getLogger(__name__)
app = FastAPI(title="ZeroToShip API", version="1.0.0")

class WorkflowRequest(BaseModel):
    idea: str
    workflow_name: str

class WorkflowResponse(BaseModel):
    status: str
    project_id: str
    task_id: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: dict | None = None

@app.post("/run-workflow/", response_model=WorkflowResponse, status_code=202)
async def run_workflow(request: WorkflowRequest) -> WorkflowResponse:
    project_id = f"project_{uuid.uuid4().hex[:8]}"
    project_data = {
        "id": project_id,
        "idea": request.idea,
        "workflow": request.workflow_name,
    }
    task = execute_workflow_task.delay(project_data)
    return WorkflowResponse(status="Workflow dispatched", project_id=project_id, task_id=task.id)

@app.get("/task-status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str) -> TaskStatusResponse:
    task_result = AsyncResult(task_id)
    result = task_result.get() if task_result.ready() else None
    return TaskStatusResponse(task_id=task_id, status=task_result.status, result=result)

@app.get("/health")
def health_check():
    return {"status": "ok"}