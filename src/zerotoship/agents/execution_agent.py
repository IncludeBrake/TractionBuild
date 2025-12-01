"""
Execution Agent for tractionbuild.
Handles task decomposition, planning, and execution graph creation.
"""

from typing import Dict, List, Optional, Any
from crewai import Agent
from pydantic import BaseModel, Field

from ..models.task import Task, TaskStatus, TaskPriority
from ..models.execution_graph import ExecutionGraph, GraphNode, NodeType, NodeStatus
from ..tools.graph_tools import GraphTools


class ExecutionAgentConfig(BaseModel):
    """Configuration for the Execution Agent."""
    
    name: str = Field(default="Execution Agent", description="Agent name")
    role: str = Field(default="Task Decomposition and Planning", description="Agent role")
    goal: str = Field(
        default="Break down ideas into atomic tasks and create execution graphs",
        description="Agent goal"
    )
    backstory: str = Field(
        default="""You are an expert project manager and systems architect with 15+ years 
        of experience in task decomposition, dependency mapping, and execution planning. 
        You have successfully planned and executed hundreds of complex projects.""",
        description="Agent backstory"
    )
    verbose: bool = Field(default=True, description="Enable verbose logging")
    allow_delegation: bool = Field(default=False, description="Allow task delegation")
    max_iterations: int = Field(default=5, description="Maximum iterations for planning")


class ExecutionAgent:
    """Execution Agent for task decomposition and planning."""
    
    def __init__(self, config: Optional[ExecutionAgentConfig] = None):
        """Initialize the Execution Agent."""
        self.config = config or ExecutionAgentConfig()
        self.tools = [GraphTools()]
        self.agent = self._create_agent()
    
    def _create_agent(self) -> Agent:
        """Create the CrewAI agent instance."""
        return Agent(
            role=self.config.role,
            goal=self.config.goal,
            backstory=self.config.backstory,
            verbose=self.config.verbose,
            allow_delegation=self.config.allow_delegation,
            max_iter=self.config.max_iterations
        )
    
    async def create_execution_plan(
        self, 
        idea: str, 
        validation_result: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionGraph:
        """
        Create an execution plan from an idea and validation result.
        
        Args:
            idea: The original idea
            validation_result: Result from validation
            context: Additional context
            
        Returns:
            ExecutionGraph with tasks and dependencies
        """
        # Placeholder implementation
        return ExecutionGraph(
            id="exec_graph_1",
            project_id="project_1",
            name="Execution Plan",
            description=f"Execution plan for: {idea}",
            nodes=[],
            is_active=True
        )
    
    async def decompose_tasks(
        self, 
        idea: str, 
        scope: Dict[str, Any]
    ) -> List[Task]:
        """
        Decompose an idea into atomic tasks.
        
        Args:
            idea: The idea to decompose
            scope: Scope definition
            
        Returns:
            List of atomic tasks
        """
        # Placeholder implementation
        return [
            Task(
                id="task_1",
                project_id="project_1",
                name="Market Research",
                description="Conduct initial market research",
                status=TaskStatus.PENDING,
                priority=TaskPriority.HIGH
            ),
            Task(
                id="task_2", 
                project_id="project_1",
                name="MVP Design",
                description="Design MVP features",
                status=TaskStatus.PENDING,
                priority=TaskPriority.HIGH
            )
        ]
    
    async def create_dependency_graph(
        self, 
        tasks: List[Task]
    ) -> Dict[str, Any]:
        """
        Create a dependency graph from tasks.
        
        Args:
            tasks: List of tasks
            
        Returns:
            Dependency graph structure
        """
        # Placeholder implementation
        return {
            "nodes": [task.dict() for task in tasks],
            "edges": [],
            "metadata": {
                "total_tasks": len(tasks),
                "graph_type": "dependency"
            }
        } 