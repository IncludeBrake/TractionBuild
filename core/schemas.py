# src/tractionbuild/core/schemas.py
from enum import Enum
from typing import List
from pydantic import BaseModel, Field

class ProjectStatus(str, Enum):
    """Enumeration for project lifecycle states."""
    IDEA_VALIDATION = "IDEA_VALIDATION"
    EXECUTION_PLANNING = "EXECUTION_PLANNING"
    BUILD_PHASE = "BUILD_PHASE"
    MARKETING_LAUNCH = "MARKETING_LAUNCH"
    QUALITY_ASSURANCE = "QUALITY_ASSURANCE"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"

class ProjectCreate(BaseModel):
    """Schema for creating a new project via the API."""
    name: str
    description: str
    hypothesis: str
    target_avatars: List[str]
    workflow: str = "validation_and_launch"