"""
Task model for ZeroToShip.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class TaskPriority(str, Enum):
    """Task priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Task(BaseModel):
    """Task model."""
    
    id: str = Field(description="Unique task identifier")
    project_id: str = Field(description="Parent project ID")
    name: str = Field(description="Task name")
    description: str = Field(description="Task description")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Task status")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Task priority")
    agent_id: Optional[str] = Field(default=None, description="Assigned agent ID")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    started_at: Optional[datetime] = Field(default=None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")
    estimated_effort: Optional[int] = Field(default=None, description="Estimated effort in hours")
    actual_effort: Optional[int] = Field(default=None, description="Actual effort in hours")
    dependencies: List[str] = Field(default_factory=list, description="Task dependencies")
    tags: List[str] = Field(default_factory=list, description="Task tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        use_enum_values = True 