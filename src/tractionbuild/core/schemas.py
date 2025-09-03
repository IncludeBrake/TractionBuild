from enum import Enum
from pydantic import BaseModel
from typing import Optional

class ProjectStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    # Add other fields as needed