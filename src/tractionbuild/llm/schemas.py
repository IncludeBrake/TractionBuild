from __future__ import annotations
from pydantic import BaseModel, Field, ValidationError, constr
from typing import Optional, List, Dict, Any

class ExtractCompanySignals(BaseModel):
    company: constr(strip_whitespace=True, min_length=1)
    website: Optional[str] = None
    topics: List[str] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)  # <- NEW
    # add more fields over time (funding_round, headcount, etc.)

class Abstention(BaseModel):
    abstained: bool = True
    reasons: List[str] = Field(default_factory=list)

class ExtractEnvelope(BaseModel):
    ok: bool
    model: str
    usage: Dict[str, int] = Field(default_factory=lambda: {"prompt_tokens":0,"completion_tokens":0})
    data: Optional[ExtractCompanySignals] = None
    abstain: Optional[Abstention] = None
    raw: Optional[Dict[str, Any]] = None
