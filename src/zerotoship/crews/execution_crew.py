"""
Execution Crew for ZeroToShip.
Orchestrates task decomposition, planning, and execution management.
"""

import asyncio
from typing import Dict, List, Optional, Any
from crewai import Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from pydantic import BaseModel, Field

from ..agents.execution_agent import ExecutionAgent
from ..tools.code_tools import CodeTools
from ..models.task import Task as TaskModel
from ..core.project_meta_memory import ProjectMetaMemoryManager


class ExecutionCrewConfig(BaseModel):
    """Configuration for the Execution Crew."""
    
    enable_memory_learning: bool = Field(default=True, description="Enable memory learning")
    enable_task_decomposition: bool = Field(default=True, description="Enable task decomposition")
    max_execution_iterations: int = Field(default=5, description="Maximum execution iterations")
    enable_dependency_mapping: bool = Field(default=True, description="Enable dependency mapping")
    enable_resource_planning: bool = Field(default=True, description="Enable resource planning")


@CrewBase
class ExecutionCrew:
    """Execution Crew for comprehensive task planning and execution management."""
    
    def __init__(self, config: Optional[ExecutionCrewConfig] = None):
        """Initialize the Execution Crew."""
        self.config = config or ExecutionCrewConfig()
        self.memory_manager = ProjectMetaMemoryManager()
        self.execution_agent = ExecutionAgent()
        
    @agent
    def task_decomposer(self) -> ExecutionAgent:
        """Task decomposition agent for breaking down complex projects."""
        return self.execution_agent
    
    @agent
    def dependency_mapper(self) -> ExecutionAgent:
        """Dependency mapping agent for identifying task relationships."""
        return ExecutionAgent()
    
    @agent
    def resource_planner(self) -> ExecutionAgent:
        """Resource planning agent for allocation and scheduling."""
        return ExecutionAgent()
    
    @agent
    def timeline_architect(self) -> ExecutionAgent:
        """Timeline architect for creating execution schedules."""
        return ExecutionAgent()
    
    @agent
    def execution_synthesizer(self) -> ExecutionAgent:
        """Execution synthesizer for comprehensive planning."""
        return ExecutionAgent()

    @task
    def project_decomposition(self) -> Task:
        """Decompose project into manageable tasks."""
        return Task(
            description="""
            Break down the validated project into detailed, actionable tasks.
            
            Focus on:
            1. Core feature requirements
            2. Technical implementation steps
            3. User experience components
            4. Integration requirements
            5. Testing and validation needs
            
            Provide granular task breakdown with clear deliverables.
            """,
            agent=self.task_decomposer(),
            expected_output="Comprehensive task decomposition with detailed task descriptions."
        )

    @task
    def dependency_analysis(self) -> Task:
        """Analyze task dependencies and relationships."""
        return Task(
            description="""
            Map task dependencies and critical path analysis.
            
            Analyze:
            1. Task dependencies and prerequisites
            2. Critical path identification
            3. Parallel execution opportunities
            4. Bottleneck identification
            5. Risk mitigation through dependency management
            
            Provide dependency graph and critical path analysis.
            """,
            agent=self.dependency_mapper(),
            expected_output="Dependency map with critical path and parallel execution opportunities.",
            context=["project_decomposition"]
        )

    @task
    def resource_allocation_planning(self) -> Task:
        """Plan resource allocation and team requirements."""
        return Task(
            description="""
            Plan resource allocation and team requirements.
            
            Plan:
            1. Team size and skill requirements
            2. Technology stack and tools
            3. Budget allocation across phases
            4. External dependencies and vendors
            5. Infrastructure and environment needs
            
            Provide detailed resource plan with cost estimates.
            """,
            agent=self.resource_planner(),
            expected_output="Comprehensive resource plan with team, budget, and technology allocation.",
            context=["project_decomposition", "dependency_analysis"]
        )

    @task
    def timeline_construction(self) -> Task:
        """Construct detailed project timeline."""
        return Task(
            description="""
            Create detailed project timeline with milestones.
            
            Construct:
            1. Phase-based timeline with milestones
            2. Sprint planning and iterations
            3. Buffer time for uncertainties
            4. Integration and testing phases
            5. Launch preparation timeline
            
            Provide realistic timeline with contingency planning.
            """,
            agent=self.timeline_architect(),
            expected_output="Detailed project timeline with milestones and contingency planning.",
            context=["dependency_analysis", "resource_allocation_planning"]
        )

    @task
    def execution_plan_synthesis(self) -> Task:
        """Synthesize comprehensive execution plan."""
        return Task(
            description="""
            Synthesize all planning elements into comprehensive execution plan.
            
            Integrate:
            1. Task decomposition and dependencies
            2. Resource allocation and team structure
            3. Timeline and milestone planning
            4. Risk mitigation strategies
            5. Success metrics and KPIs
            
            Provide complete execution blueprint with monitoring framework.
            """,
            agent=self.execution_synthesizer(),
            expected_output="Comprehensive execution plan with monitoring and success metrics.",
            context=["project_decomposition", "dependency_analysis", "resource_allocation_planning", "timeline_construction"]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Execution Crew."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )

    async def create_execution_plan(self, validated_idea: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create comprehensive execution plan for validated idea.
        
        Args:
            validated_idea: Validated idea with market research
            context: Additional context for planning
            
        Returns:
            Comprehensive execution plan
        """
        # Store validated idea in memory
        self.memory_manager.add_success_pattern(
            pattern={"validated_idea": validated_idea, "context": context},
            project_id="execution_crew",
            agent_id="execution_crew",
            confidence_score=0.8
        )
        
        # Execute the crew workflow
        inputs = {
            "validated_idea": validated_idea,
            "context": context or {},
            "execution_steps": [
                "project_decomposition",
                "dependency_analysis",
                "resource_allocation_planning",
                "timeline_construction",
                "execution_plan_synthesis"
            ]
        }
        
        result = await self.crew().kickoff(inputs=inputs)
        
        # Store execution plan in memory
        self.memory_manager.add_success_pattern(
            pattern={"execution_plan": result},
            project_id="execution_crew",
            agent_id="execution_crew",
            confidence_score=0.9
        )
        
        return {
            "tasks": result.get("tasks", []),
            "dependencies": result.get("dependencies", []),
            "timeline": result.get("timeline", "TBD"),
            "resources": result.get("resources", {}),
            "estimated_effort": result.get("estimated_effort", "TBD"),
            "critical_path": result.get("critical_path", []),
            "milestones": result.get("milestones", []),
            "success_metrics": result.get("success_metrics", [])
        }

    async def decompose_tasks(self, project_scope: str, constraints: Optional[Dict[str, Any]] = None) -> List[TaskModel]:
        """
        Decompose project scope into detailed tasks.
        
        Args:
            project_scope: Project scope description
            constraints: Project constraints
            
        Returns:
            List of detailed tasks
        """
        # Store task decomposition in memory
        self.memory_manager.add_success_pattern(
            pattern={"task_decomposition": {"scope": project_scope, "constraints": constraints}},
            project_id="execution_crew",
            agent_id="execution_crew",
            confidence_score=0.8
        )
        
        # Execute task decomposition
        inputs = {
            "project_scope": project_scope,
            "constraints": constraints or {},
            "decomposition_type": "task_breakdown"
        }
        
        result = await self.crew().kickoff(inputs=inputs)
        
        # Convert to TaskModel objects
        tasks = []
        for task_data in result.get("tasks", []):
            task = TaskModel(
                id=task_data.get("id", ""),
                name=task_data.get("name", ""),
                description=task_data.get("description", ""),
                status=task_data.get("status", "pending"),
                priority=task_data.get("priority", "medium"),
                estimated_effort=task_data.get("estimated_effort", 0),
                dependencies=task_data.get("dependencies", [])
            )
            tasks.append(task)
        
        return tasks

    async def create_dependency_graph(self, tasks: List[TaskModel]) -> Dict[str, Any]:
        """
        Create dependency graph for task execution.
        
        Args:
            tasks: List of tasks to analyze
            
        Returns:
            Dependency graph with critical path
        """
        # Store dependency analysis in memory
        self.memory_manager.add_success_pattern(
            pattern={"dependency_graph": {"tasks": [task.dict() for task in tasks]}},
            project_id="execution_crew",
            agent_id="execution_crew",
            confidence_score=0.8
        )
        
        # Execute dependency analysis
        inputs = {
            "tasks": [task.dict() for task in tasks],
            "analysis_type": "dependency_mapping"
        }
        
        result = await self.crew().kickoff(inputs=inputs)
        
        return {
            "dependencies": result.get("dependencies", {}),
            "critical_path": result.get("critical_path", []),
            "parallel_tasks": result.get("parallel_tasks", []),
            "bottlenecks": result.get("bottlenecks", []),
            "optimization_opportunities": result.get("optimization_opportunities", [])
        }

    async def run_async(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the execution crew asynchronously.
        
        Args:
            project_data: Project data to process
            
        Returns:
            Execution plan and task breakdown
        """
        try:
            # Extract validated idea from project data
            validated_idea = {
                "idea": project_data.get('idea', ''),
                "validation": project_data.get('validation', {}),
                "market_analysis": project_data.get('market_analysis', {})
            }
            
            # Create execution plan
            execution_plan = await self.create_execution_plan(validated_idea, project_data)
            
            # Decompose tasks
            tasks = await self.decompose_tasks(project_data.get('idea', ''), {
                "budget": project_data.get('budget'),
                "timeline": project_data.get('timeline')
            })
            
            # Create dependency graph
            dependency_graph = await self.create_dependency_graph(tasks)
            
            # Combine results
            result = {
                "execution_plan": execution_plan,
                "tasks": [task.dict() for task in tasks],
                "dependency_graph": dependency_graph,
                "status": "completed",
                "confidence": 0.85
            }
            
            return result
            
        except Exception as e:
            return {
                "error": str(e),
                "status": "failed",
                "confidence": 0.0
            } 