"""
FastAPI application for ZeroToShip.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any

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