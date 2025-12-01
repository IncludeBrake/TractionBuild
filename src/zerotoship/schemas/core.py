from pydantic import BaseModel, Field, HttpUrl
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime

class AvatarType(str, Enum):
    STARTUP = "startup_entrepreneur"; SME = "sme"
    INVESTOR = "investor_incubator"; CORP_LAB = "corporate_innovation_lab"

class ProjectStatus(str, Enum):
    IDEA_VALIDATION="IDEA_VALIDATION"; EXECUTION_PLANNING="EXECUTION_PLANNING"
    BUILD_PHASE="BUILD_PHASE"; MARKETING_LAUNCH="MARKETING_LAUNCH"
    QUALITY_ASSURANCE="QUALITY_ASSURANCE"; COMPLETED="COMPLETED"; ERROR="ERROR"

class ProjectCreate(BaseModel):
    name: str
    description: str
    hypothesis: str
    target_avatars: List[AvatarType] = Field(min_items=1)
    workflow: str = "validation_and_launch"

class Project(BaseModel):
    id: str; name: str; description: str
    state: ProjectStatus; created_at: datetime; updated_at: datetime
    metadata: Dict[str, Any] = {}; results: Dict[str, Any] = {}

class AvatarProfile(BaseModel):
    avatar: AvatarType; pains: List[str]; gains: List[str]
    jobs_to_be_done: List[str]; buying_constraints: List[str] = []
    budget_range_usd: Optional[List[int]] = None; procurement_notes: Optional[str] = None

class ValidationOutput(BaseModel):
    go_recommendation: bool; confidence: float
    avatars: List[AvatarProfile]; mvp_features: List[str]
    risks: List[str]; findings: List[Dict[str, Any]] = []

class AdvisoryDecision(BaseModel):
    approved: bool; rationale: str
    must_haves: List[str] = []; cut_scope: List[str] = []
    kpis: Dict[str, float] = {}
