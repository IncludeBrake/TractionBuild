"""
FastAPI application for ZeroToShip.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import time
import logging
from typing import Dict, Any, Optional
import asyncpg
from neo4j import AsyncGraphDatabase

from ..schemas import ProjectCreate, Project, ProjectStatus
from ..core.workflow_engine import WorkflowEngine
from ..database.projects import ProjectsDAO
from ..database.logs import ExecutionLogsDAO
from ..database.graph import GraphDAO
from ..crews.adapters import ValidatorAdapter, AdvisoryAdapter
from ..crews.validator_crew import ValidatorCrew
from ..crews.advisory_board_crew import AdvisoryBoardCrew

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Metrics counters
REQUEST_COUNT = {"total": 0, "success": 0, "error": 0}
REQUEST_LATENCY = []
PROJECT_CREATED = 0
PROJECT_RETRIEVED = 0

app = FastAPI(title="ZeroToShip API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state (in production, use dependency injection)
db_pool = None
neo4j_driver = None
workflow_engine = None
projects_dao = None
logs_dao = None
graph_dao = None

@app.on_event("startup")
async def startup_event():
    """Initialize database connections and workflow engine."""
    global db_pool, neo4j_driver, workflow_engine, projects_dao, logs_dao, graph_dao
    
    # Initialize Postgres
    db_pool = await asyncpg.create_pool(
        host="localhost",
        port=5432,
        user="postgres",
        password="password",
        database="zerotoship"
    )
    
    # Initialize Neo4j
    neo4j_driver = AsyncGraphDatabase.driver(
        "neo4j://localhost:7687",
        auth=("neo4j", "password")
    )
    
    # Initialize DAOs
    projects_dao = ProjectsDAO(db_pool)
    logs_dao = ExecutionLogsDAO(db_pool)
    graph_dao = GraphDAO(neo4j_driver)
    
    # Initialize crews and adapters
    validator_crew = ValidatorCrew()
    advisory_crew = AdvisoryBoardCrew()
    
    validator_adapter = ValidatorAdapter(validator_crew)
    advisory_adapter = AdvisoryAdapter(advisory_crew)
    
    # Create registry
    registry = {
        "validator": validator_adapter,
        "advisory": advisory_adapter
    }
    
    workflow_engine = WorkflowEngine(registry)

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up database connections."""
    if db_pool:
        await db_pool.close()
    if neo4j_driver:
        await neo4j_driver.close()

async def run_workflow_background(project_id: str, project_data: ProjectCreate):
    """Background task to run the workflow."""
    start_time = time.time()
    
    try:
        # Get the project
        project = await projects_dao.get_project(project_id)
        if not project:
            logger.error(f"Project {project_id} not found for workflow execution")
            return
        
        # Run workflow
        workflow_result = await workflow_engine.run(project.model_dump())
        
        # Update project with results
        await projects_dao.update_project_state(
            project_id, 
            ProjectStatus(workflow_result["project"]["state"]),
            workflow_result.get("artifacts")
        )
        
        # Log executions
        for agent_name, result in workflow_result.get("artifacts", {}).items():
            duration_ms = int((time.time() - start_time) * 1000)
            await logs_dao.log_execution(
                project_id, agent_name, "success", duration_ms, result
            )
            
            # Create artifact in Neo4j
            await graph_dao.create_artifact_node(project_id, agent_name, result)
        
        logger.info(f"Workflow completed for project {project_id}")
        
    except Exception as e:
        logger.error(f"Workflow failed for project {project_id}: {str(e)}")
        duration_ms = int((time.time() - start_time) * 1000)
        await logs_dao.log_execution(project_id, "workflow", "error", duration_ms, error=str(e))
        await projects_dao.update_project_state(project_id, ProjectStatus.ERROR)

@app.post("/api/v1/projects", response_model=Dict[str, str])
async def create_project(project_data: ProjectCreate, background_tasks: BackgroundTasks):
    """Create a new project and start background workflow."""
    global PROJECT_CREATED
    
    start_time = time.time()
    REQUEST_COUNT["total"] += 1
    
    try:
        # Create project in database
        project = await projects_dao.create_project(project_data)
        
        # Create project node in Neo4j
        await graph_dao.create_project_node(project.id, project.model_dump())
        
        # Start background workflow
        background_tasks.add_task(run_workflow_background, project.id, project_data)
        
        PROJECT_CREATED += 1
        REQUEST_COUNT["success"] += 1
        REQUEST_LATENCY.append(time.time() - start_time)
        
        return {"project_id": project.id}
        
    except Exception as e:
        REQUEST_COUNT["error"] += 1
        logger.error(f"Failed to create project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/projects/{project_id}", response_model=Dict[str, Any])
async def get_project(project_id: str):
    """Get project with artifacts."""
    global PROJECT_RETRIEVED
    
    start_time = time.time()
    REQUEST_COUNT["total"] += 1
    
    try:
        # Get project from Postgres
        project = await projects_dao.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get artifacts from Neo4j
        artifacts = await graph_dao.get_project_artifacts(project_id)
        
        # Get execution logs
        logs = await logs_dao.get_project_logs(project_id)
        
        PROJECT_RETRIEVED += 1
        REQUEST_COUNT["success"] += 1
        REQUEST_LATENCY.append(time.time() - start_time)
        
        return {
            "project": project.model_dump(),
            "artifacts": artifacts,
            "logs": logs
        }
        
    except HTTPException:
        raise
    except Exception as e:
        REQUEST_COUNT["error"] += 1
        logger.error(f"Failed to get project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/projects/{project_id}/status")
async def get_project_status(project_id: str):
    """Get project status and progress."""
    start_time = time.time()
    REQUEST_COUNT["total"] += 1
    
    try:
        project = await projects_dao.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        logs = await logs_dao.get_project_logs(project_id)
        
        # Calculate progress
        total_steps = 2  # validator + advisory
        completed_steps = len([log for log in logs if log["status"] == "success"])
        progress = (completed_steps / total_steps) * 100 if total_steps > 0 else 0
        
        current_step = "completed" if project.state == ProjectStatus.COMPLETED else "running"
        
        REQUEST_COUNT["success"] += 1
        REQUEST_LATENCY.append(time.time() - start_time)
        
        return {
            "state": project.state.value,
            "progress": progress,
            "current_step": current_step,
            "completed_steps": completed_steps,
            "total_steps": total_steps
        }
        
    except HTTPException:
        raise
    except Exception as e:
        REQUEST_COUNT["error"] += 1
        logger.error(f"Failed to get project status {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def get_metrics():
    """Prometheus-style metrics."""
    avg_latency = sum(REQUEST_LATENCY) / len(REQUEST_LATENCY) if REQUEST_LATENCY else 0
    
    return {
        "zerotoship_requests_total": REQUEST_COUNT["total"],
        "zerotoship_requests_success": REQUEST_COUNT["success"],
        "zerotoship_requests_error": REQUEST_COUNT["error"],
        "zerotoship_request_duration_seconds": avg_latency,
        "zerotoship_projects_created": PROJECT_CREATED,
        "zerotoship_projects_retrieved": PROJECT_RETRIEVED
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check Postgres
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        
        # Check Neo4j
        async with neo4j_driver.session() as session:
            await session.run("RETURN 1")
        
        return {"status": "healthy", "databases": ["postgres", "neo4j"]}
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unhealthy") 