"""
Project model for ZeroToShip.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class ProjectStatus(str, Enum):
    """Project status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class Project(BaseModel):
    """Project model."""
    
    id: str = Field(description="Unique project identifier")
    name: str = Field(description="Project name")
    description: str = Field(description="Project description")
    status: ProjectStatus = Field(default=ProjectStatus.PENDING, description="Project status")
    user_id: str = Field(description="User who created the project")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")
    tags: List[str] = Field(default_factory=list, description="Project tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        use_enum_values = True 