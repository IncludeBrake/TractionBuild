from crewai import Crew, Agent, Task, Process
from .base_crew import BaseCrew # Import our standardized base class

<<<<<<< Updated upstream
class ExecutionCrew(BaseCrew):
    """
    The ExecutionCrew is a specialized team of AI agents that translates a
    validated idea into a comprehensive, actionable execution plan, complete
    with tasks, dependencies, timelines, and resource allocation.
    """

    def _create_crew(self) -> Crew:
        """
        Defines the agents and tasks that form the ExecutionCrew.
        This method is called by the BaseCrew's __init__.
        """

        # 1. --- DEFINE SPECIALIZED AGENTS ---
        
        task_decomposer = Agent(
            role="Lead Systems Analyst",
            goal="Decompose a high-level project idea into a granular list of atomic, actionable engineering tasks.",
            backstory="You are a meticulous systems analyst with a deep understanding of software development. You excel at breaking down complex requirements into clear, unambiguous tasks that a development team can execute.",
            tools=[],
            allow_delegation=False,
            verbose=True
        )

        dependency_mapper = Agent(
            role="Technical Project Manager",
            goal="Analyze a list of tasks to identify all dependencies, map them out, and identify the project's critical path.",
            backstory="You are an expert project manager with a knack for seeing the big picture. You can instantly identify which tasks block others, where work can be parallelized, and what the most critical sequence of events is for a successful project.",
            tools=[], # e.g., MermaidTools
            allow_delegation=False,
            verbose=True
        )

        resource_planner = Agent(
            role="Resource Allocation Specialist",
            goal="Create a detailed plan for allocating team members, budget, and technical resources to a project.",
            backstory="You are a strategic planner with a background in finance and project management. You are an expert at creating realistic budgets and assigning the right people to the right tasks to maximize efficiency.",
            tools=[],
            allow_delegation=False,
            verbose=True
        )
        
        execution_synthesizer = Agent(
            role="Director of Project Execution",
            goal="Synthesize all planning documents (task list, dependency graph, resource plan) into a single, comprehensive, and final execution blueprint.",
            backstory="You are the ultimate authority on project planning. Your job is to review all inputs, ensure they are coherent and complete, and produce the final, authoritative execution plan that the BuilderCrew will follow.",
            tools=[],
            allow_delegation=False,
            verbose=True
        )

        # 2. --- DEFINE THE SEQUENTIAL TASKS ---

        task_decomposition = Task(
            description="Based on the validated idea from the project data, break down the project into a list of granular, atomic tasks required for completion.",
            expected_output="A detailed list of tasks, each with a clear title and a description of what needs to be done.",
            agent=task_decomposer
        )

        task_dependency_mapping = Task(
            description="Analyze the list of tasks and map out all dependencies. Identify which tasks can be done in parallel and determine the critical path.",
            expected_output="A dependency graph (in Mermaid format) and a list of tasks that form the critical path.",
            agent=dependency_mapper,
            context=[task_decomposition] # Correctly references the Task object
        )

        task_resource_planning = Task(
            description="Create a resource plan based on the decomposed tasks. Estimate the required team skills, technology stack, and a high-level budget allocation.",
            expected_output="A resource plan document outlining team, technology, and budget requirements.",
            agent=resource_planner,
            context=[task_decomposition]
        )
        
        task_synthesis = Task(
            description="Synthesize the task list, dependency graph, and resource plan into a final, comprehensive execution blueprint. This blueprint will be the master document for the BuilderCrew.",
            expected_output="A final, unified execution plan in a well-structured document.",
            agent=execution_synthesizer,
            context=[task_decomposition, task_dependency_mapping, task_resource_planning]
        )
        
        # 3. --- ASSEMBLE AND RETURN THE CREW ---
        
        return Crew(
            agents=[task_decomposer, dependency_mapper, resource_planner, execution_synthesizer],
            tasks=[task_decomposition, task_dependency_mapping, task_resource_planning, task_synthesis],
            process=Process.sequential,
            verbose=True
        )
=======
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
>>>>>>> Stashed changes
