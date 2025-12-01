"""
Launch Crew for tractionbuild.
Orchestrates launch preparation, execution, and post-launch activities.
"""

import asyncio
from typing import Dict, List, Optional, Any
from crewai import Crew, Process, Task
from pydantic import BaseModel, Field

from ..agents.launch_agent import LaunchAgent
from ..tools.celery_execution_tool import CeleryExecutionTool
from ..core.project_meta_memory import ProjectMetaMemoryManager
from .base_crew import BaseCrew

class LaunchCrewConfig(BaseModel):
    """Configuration for the Launch Crew."""
    enable_memory_learning: bool = Field(default=True, description="Enable memory learning")
    enable_launch_preparation: bool = Field(default=True, description="Enable launch preparation")
    max_launch_iterations: int = Field(default=3, description="Maximum launch iterations")
    enable_post_launch_analysis: bool = Field(default=True, description="Enable post-launch analysis")
    enable_crisis_management: bool = Field(default=True, description="Enable crisis management")

class LaunchCrew(BaseCrew):
    """Launch Crew for comprehensive launch preparation and execution."""
    
    def __init__(self, project_data: Dict[str, Any], config: Optional[LaunchCrewConfig] = None):
        super().__init__(project_data)
        self.config = config or LaunchCrewConfig()
        self.memory_manager = ProjectMetaMemoryManager()
        self.launch_agent = LaunchAgent()
        self.celery_executor = CeleryExecutionTool()

    def _create_crew(self) -> Crew:
        """Create the Launch Crew with agents and tasks."""
        agents = [
            self.launch_agent(name="Launch Preparer", role="Launch preparation expert"),
            self.launch_agent(name="Execution Coordinator", role="Launch day coordinator"),
            self.launch_agent(name="Post-Launch Analyst", role="Post-launch analysis specialist"),
            self.launch_agent(name="Crisis Manager", role="Crisis management expert"),
            self.launch_agent(name="Momentum Builder", role="Momentum sustaining strategist"),
        ]

        # Create tasks separately to avoid forward references
        task1 = Task(
            description="""
            Prepare comprehensive launch strategy and execution checklist.
            Prepare: 1. Launch timeline, 2. Pre-launch marketing,
            3. Technical readiness, 4. Team coordination, 5. Crisis planning.
            Provide launch preparation.
            """,
            agent=agents[0],
            expected_output="Comprehensive launch preparation with checklist."
        )
        
        task2 = Task(
            description="""
            Execute launch day activities and coordinate efforts.
            Execute: 1. Timeline execution, 2. Real-time monitoring,
            3. Team coordination, 4. Customer support, 5. Performance optimization.
            Provide execution report.
            """,
            agent=agents[1],
            expected_output="Launch day execution report with metrics.",
            context=[task1]
        )
        
        task3 = Task(
            description="""
            Analyze launch performance and gather insights.
            Analyze: 1. Performance metrics, 2. User acquisition,
            3. Technical stability, 4. Customer feedback, 5. Market response.
            Provide analysis.
            """,
            agent=agents[2],
            expected_output="Comprehensive post-launch analysis.",
            context=[task2]
        )
        
        task4 = Task(
            description="""
            Plan crisis management and issue resolution strategies.
            Plan: 1. Crisis scenarios, 2. Communication protocols,
            3. Escalation procedures, 4. Recovery strategies, 5. Learning processes.
            Provide framework.
            """,
            agent=agents[3],
            expected_output="Crisis management framework.",
            context=[task1]
        )
        
        task5 = Task(
            description="""
            Develop strategies to sustain launch momentum.
            Develop: 1. Post-launch marketing, 2. User retention,
            3. Feature planning, 4. Community building, 5. Success metrics.
            Provide strategy.
            """,
            agent=agents[4],
            expected_output="Momentum sustaining strategy with roadmap.",
            context=[task3, task4]
        )
        
        tasks = [task1, task2, task3, task4, task5]

        return Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
        )

    async def _execute_crew(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the Launch Crew using distributed execution."""
        task_type = next(iter(inputs.keys()), "prepare_launch")
        task_result = await self.celery_executor.execute_task(
            lambda: self.crew.kickoff_async(inputs=inputs)
        )
        result = task_result.result() if task_result else {}
        return result.get(task_type, {})

    async def prepare_launch(self, product_info: Dict[str, Any], launch_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        project_data = self.project_data.copy()
        project_data.update({"product_info": product_info, "launch_context": launch_context})
        return await self._execute_crew(project_data)

    async def execute_launch(self, launch_plan: Dict[str, Any]) -> Dict[str, Any]:
        project_data = self.project_data.copy()
        project_data.update({"launch_plan": launch_plan})
        return await self._execute_crew(project_data)

    async def analyze_launch_performance(self, launch_data: Dict[str, Any]) -> Dict[str, Any]:
        project_data = self.project_data.copy()
        project_data.update({"launch_data": launch_data})
        return await self._execute_crew(project_data)