from enum import Enum
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ProjectStatus(Enum):
    IDEA_VALIDATION = "idea_validation"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed" 
    ERROR = "error"

class ProjectCreate(BaseModel):
    name: str
    description: str
    hypothesis: Optional[str] = None
    target_avatars: Optional[List[str]] = []
    workflow: str = "default_software_build"