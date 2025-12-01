"""
Execution graph models for tractionbuild.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class NodeType(str, Enum):
    """Node type enumeration."""
    TASK = "task"
    DECISION = "decision"
    CONDITION = "condition"
    START = "start"
    END = "end"
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"


class NodeStatus(str, Enum):
    """Node status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


class GraphNode(BaseModel):
    """Graph node model."""
    
    id: str = Field(description="Unique node identifier")
    name: str = Field(description="Node name")
    node_type: NodeType = Field(description="Node type")
    status: NodeStatus = Field(default=NodeStatus.PENDING, description="Node status")
    description: Optional[str] = Field(default=None, description="Node description")
    agent_id: Optional[str] = Field(default=None, description="Assigned agent ID")
    task_id: Optional[str] = Field(default=None, description="Associated task ID")
    dependencies: List[str] = Field(default_factory=list, description="Node dependencies")
    children: List[str] = Field(default_factory=list, description="Child node IDs")
    parent: Optional[str] = Field(default=None, description="Parent node ID")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    started_at: Optional[datetime] = Field(default=None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        use_enum_values = True


class ExecutionGraph(BaseModel):
    """Execution graph model."""
    
    id: str = Field(description="Unique graph identifier")
    project_id: str = Field(description="Associated project ID")
    name: str = Field(description="Graph name")
    description: Optional[str] = Field(default=None, description="Graph description")
    nodes: List[GraphNode] = Field(default_factory=list, description="Graph nodes")
    root_node_id: Optional[str] = Field(default=None, description="Root node ID")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    is_active: bool = Field(default=True, description="Graph active status")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        use_enum_values = True 