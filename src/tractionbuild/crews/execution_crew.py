"""
Execution Crew for tractionbuild.
Orchestrates task decomposition, planning, and execution management.
"""

import asyncio
from typing import Dict, List, Optional, Any
from crewai import Crew, Process, Task
from pydantic import BaseModel, Field

from ..agents.execution_agent import ExecutionAgent
from ..tools.code_tools import CodeTools
from ..tools.celery_execution_tool import CeleryExecutionTool
from ..models.task import Task as TaskModel
from ..core.project_meta_memory import ProjectMetaMemoryManager
from .base_crew import BaseCrew
from ..utils.llm_factory import get_llm

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
        self.celery_executor = CeleryExecutionTool()

    def _create_crew(self) -> Crew:
        """Create the Execution Crew with agents and tasks."""
        # Get LLM from the factory
        llm = get_llm()
        
        agents = [
            self.execution_agent(name="Task Decomposer", role="Task decomposition expert", llm=llm),
            self.execution_agent(name="Dependency Mapper", role="Dependency mapping specialist", llm=llm),
            self.execution_agent(name="Resource Planner", role="Resource allocation planner", llm=llm),
            self.execution_agent(name="Timeline Architect", role="Timeline construction expert", llm=llm),
            self.execution_agent(name="Execution Synthesizer", role="Execution plan synthesizer", llm=llm),
        ]

        # Create tasks separately to avoid forward references
        task1 = Task(
            description="""
            Break down the validated project into detailed, actionable tasks.
            Focus on: 1. Core feature requirements, 2. Technical steps,
            3. UI components, 4. Integration needs, 5. Testing.
            Provide granular task breakdown.
            """,
            agent=agents[0],
            expected_output="Comprehensive task decomposition with detailed descriptions."
        )
        
        task2 = Task(
            description="""
            Map task dependencies and critical path analysis.
            Analyze: 1. Task dependencies, 2. Critical path,
            3. Parallel opportunities, 4. Bottlenecks, 5. Risk mitigation.
            Provide dependency graph.
            """,
            agent=agents[1],
            expected_output="Dependency map with critical path.",
            context=[task1]
        )
        
        task3 = Task(
            description="""
            Plan resource allocation and team requirements.
            Plan: 1. Team size/skills, 2. Tech stack, 3. Budget,
            4. External dependencies, 5. Infrastructure.
            Provide resource plan.
            """,
            agent=agents[2],
            expected_output="Comprehensive resource plan.",
            context=[task1, task2]
        )
        
        task4 = Task(
            description="""
            Create detailed project timeline with milestones.
            Construct: 1. Phase timeline, 2. Sprint planning,
            3. Buffer time, 4. Testing phases, 5. Launch prep.
            Provide timeline.
            """,
            agent=agents[3],
            expected_output="Detailed timeline with contingencies.",
            context=[task2, task3]
        )
        
        task5 = Task(
            description="""
            Synthesize execution plan.
            Integrate: 1. Tasks, 2. Dependencies, 3. Resources,
            4. Timeline, 5. Risk strategies, 6. KPIs.
            Provide blueprint.
            """,
            agent=agents[4],
            expected_output="Comprehensive execution plan with monitoring.",
            context=[task1, task2, task3, task4]
        )
        
        tasks = [task1, task2, task3, task4, task5]

        return Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
        )

    async def _execute_crew(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the Execution Crew using distributed execution."""
        task_type = next(iter(inputs.keys()), "create_execution_plan")
        task_result = await self.celery_executor.execute_task(
            lambda: self.crew.kickoff_async(inputs=inputs)
        )
        result = task_result.result() if task_result else {}
        return result.get(task_type, {})

    async def create_execution_plan(self, validated_idea: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        project_data = self.project_data.copy()
        project_data.update({"validated_idea": validated_idea, "context": context})
        return await self._execute_crew(project_data)

    async def decompose_tasks(self, project_scope: str, constraints: Optional[Dict[str, Any]] = None) -> List[TaskModel]:
        project_data = self.project_data.copy()
        project_data.update({"project_scope": project_scope, "constraints": constraints})
        result = await self._execute_crew(project_data)
        tasks_data = result.get("tasks", [])
        return [TaskModel(**task) for task in tasks_data]

    async def create_dependency_graph(self, tasks: List[TaskModel]) -> Dict[str, Any]:
        project_data = self.project_data.copy()
        project_data.update({"tasks": [task.dict() for task in tasks]})
        result = await self._execute_crew(project_data)
        return result.get("dependency_graph", {})