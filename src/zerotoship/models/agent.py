"""
Agent model for ZeroToShip.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    """Agent role enumeration."""
    VALIDATOR = "validator"
    EXECUTION_GRAPH = "execution_graph"
    BUILDER = "builder"
    MARKETING = "marketing"
    FEEDBACK = "feedback"


class Agent(BaseModel):
    """Agent model."""
    
    id: str = Field(description="Unique agent identifier")
    name: str = Field(description="Agent name")
    role: AgentRole = Field(description="Agent role")
    description: str = Field(description="Agent description")
    capabilities: List[str] = Field(default_factory=list, description="Agent capabilities")
    tools: List[str] = Field(default_factory=list, description="Available tools")
    model: str = Field(default="gpt-4-turbo-preview", description="LLM model")
    temperature: float = Field(default=0.3, description="Model temperature")
    max_tokens: Optional[int] = Field(default=None, description="Maximum tokens")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    is_active: bool = Field(default=True, description="Agent active status")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        use_enum_values = True 