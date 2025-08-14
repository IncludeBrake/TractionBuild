from crewai import Crew, Agent, Task, Process
from .base_crew import BaseCrew # Import our standardized base class

import asyncio
from typing import Dict, List, Optional, Any
from crewai import Crew, Process, Task
from pydantic import BaseModel, Field

from ..agents.execution_agent import ExecutionAgent
from ..tools.code_tools import CodeTools
from ..models.task import Task as TaskModel
from ..core.project_meta_memory import ProjectMetaMemoryManager
from .base_crew import BaseCrew

class ExecutionCrewConfig(BaseModel):
    """Configuration for the Execution Crew."""
    enable_memory_learning: bool = Field(default=True, description="Enable memory learning")
    enable_task_decomposition: bool = Field(default=True, description="Enable task decomposition")
    max_execution_iterations: int = Field(default=5, description="Maximum execution iterations")
    enable_dependency_mapping: bool = Field(default=True, description="Enable dependency mapping")
    enable_resource_planning: bool = Field(default=True, description="Enable resource planning")

class ExecutionCrew(BaseCrew):
    """Execution Crew for comprehensive task planning and execution management."""
    
    def __init__(self, project_data: Dict[str, Any], config: Optional[ExecutionCrewConfig] = None):
        super().__init__(project_data)
        self.config = config or ExecutionCrewConfig()
        self.memory_manager = ProjectMetaMemoryManager()
        self.execution_agent = ExecutionAgent()

    def _create_crew(self) -> Crew:
        """Create the Execution Crew with agents and tasks."""
        agents = [
            self.execution_agent(name="Task Decomposer", role="Task decomposition expert"),
            self.execution_agent(name="Dependency Mapper", role="Dependency mapping specialist"),
            self.execution_agent(name="Resource Planner", role="Resource allocation planner"),
            self.execution_agent(name="Timeline Architect", role="Timeline construction expert"),
            self.execution_agent(name="Execution Synthesizer", role="Execution plan synthesizer"),
        ]

        tasks = [
            Task(
                description="""
                Break down the validated project into detailed, actionable tasks.
                Focus on: 1. Core feature requirements, 2. Technical steps,
                3. UI components, 4. Integration needs, 5. Testing.
                Provide granular task breakdown.
                """,
                agent=agents[0],
                expected_output="Comprehensive task decomposition with detailed descriptions."
            ),
            Task(
                description="""
                Map task dependencies and critical path analysis.
                Analyze: 1. Task dependencies, 2. Critical path,
                3. Parallel opportunities, 4. Bottlenecks, 5. Risk mitigation.
                Provide dependency graph.
                """,
                agent=agents[1],
                expected_output="Dependency map with critical path.",
                context=[tasks[0]]
            ),
            Task(
                description="""
                Plan resource allocation and team requirements.
                Plan: 1. Team size/skills, 2. Tech stack, 3. Budget,
                4. External dependencies, 5. Infrastructure.
                Provide resource plan.
                """,
                agent=agents[2],
                expected_output="Comprehensive resource plan.",
                context=[tasks[0], tasks[1]]
            ),
            Task(
                description="""
                Create detailed project timeline with milestones.
                Construct: 1. Phase timeline, 2. Sprint planning,
                3. Buffer time, 4. Testing phases, 5. Launch prep.
                Provide timeline.
                """,
                agent=agents[3],
                expected_output="Detailed timeline with contingencies.",
                context=[tasks[1], tasks[2]]
            ),
            Task(
                description="""
                Synthesize execution plan.
                Integrate: 1. Tasks, 2. Dependencies, 3. Resources,
                4. Timeline, 5. Risk strategies, 6. KPIs.
                Provide blueprint.
                """,
                agent=agents[4],
                expected_output="Comprehensive execution plan with monitoring.",
                context=[tasks[0], tasks[1], tasks[2], tasks[3]]
            ),
        ]

        return Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
        )

    async def create_execution_plan(self, validated_idea: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        project_data = self.project_data.copy()
        project_data.update({"validated_idea": validated_idea, "context": context})
        result = await self.run_async(project_data)
        return result.get("execution", {})

    async def decompose_tasks(self, project_scope: str, constraints: Optional[Dict[str, Any]] = None) -> List[TaskModel]:
        project_data = self.project_data.copy()
        project_data.update({"project_scope": project_scope, "constraints": constraints})
        result = await self.run_async(project_data)
        tasks_data = result.get("execution", {}).get("tasks", [])
        return [TaskModel(**task) for task in tasks_data]

    async def create_dependency_graph(self, tasks: List[TaskModel]) -> Dict[str, Any]:
        project_data = self.project_data.copy()
        project_data.update({"tasks": [task.dict() for task in tasks]})
        result = await self.run_async(project_data)
        return result.get("execution", {}).get("dependency_graph", {})
