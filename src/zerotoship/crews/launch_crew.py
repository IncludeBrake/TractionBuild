from crewai import Crew, Agent, Task, Process
from .base_crew import BaseCrew # Import our standardized base class

<<<<<<< Updated upstream
class LaunchCrew(BaseCrew):
    """
    The LaunchCrew is a specialized team of AI agents that orchestrates the
    entire launch process, from pre-launch strategy and day-of execution
    to post-launch analysis and momentum building.
    """

    def _create_crew(self) -> Crew:
        """
        Defines the agents and tasks that form the LaunchCrew.
        """

        # 1. --- DEFINE SPECIALIZED AGENTS ---

        launch_strategist = Agent(
            role="Head of Product Launch",
            goal="Develop a comprehensive, timeline-driven launch plan that covers all technical, marketing, and communication aspects.",
            backstory="You are a master strategist with a track record of executing flawless product launches for major tech companies. You think in terms of checklists, milestones, and contingency plans.",
            tools=[],
            allow_delegation=False,
            verbose=True
        )

        execution_coordinator = Agent(
            role="Launch Day Coordinator",
            goal="Manage and monitor all activities on launch day to ensure a smooth execution, quickly resolving any issues that arise.",
            backstory="You are the calm center of the storm on launch day. You excel at real-time monitoring, communication, and problem-solving under pressure, ensuring the entire team is synchronized.",
            tools=[],
            allow_delegation=False,
            verbose=True
        )

        post_launch_analyst = Agent(
            role="Growth Marketing Analyst",
            goal="Analyze post-launch data to measure success against KPIs, identify key insights, and recommend strategies to sustain momentum.",
            backstory="You are a data-driven analyst obsessed with metrics. You live in analytics dashboards and can turn raw data into actionable insights for user retention and growth.",
            tools=[],
            allow_delegation=False,
            verbose=True
        )

        # 2. --- DEFINE THE SEQUENTIAL TASKS ---

        task_launch_preparation = Task(
            description="Based on the project data, including validated marketing assets, create a comprehensive launch plan. "
                        "Define a detailed timeline, a pre-launch buzz-building strategy, technical readiness checks, and a crisis management protocol.",
            expected_output="A detailed launch plan document, including a multi-phase timeline, a launch day checklist, and a crisis response plan.",
            agent=launch_strategist
        )

        task_launch_execution = Task(
            description="Coordinate the activities on launch day. Monitor systems, manage communications across platforms, "
                        "and track initial performance metrics like user sign-ups and server stability.",
            expected_output="A launch day execution summary, reporting on key events, issues encountered, and initial performance metrics.",
            agent=execution_coordinator,
            context=[task_launch_preparation] # This task depends on the plan
        )
        
        task_post_launch_analysis = Task(
            description="Analyze all data from the first week post-launch. Compare results against the KPIs defined in the launch plan. "
                        "Synthesize user feedback, engagement data, and market response into a report with actionable recommendations for sustaining momentum.",
            expected_output="A comprehensive post-launch analysis report with key insights and a prioritized roadmap for growth.",
            agent=post_launch_analyst,
            context=[task_launch_execution]
        )
        
        # 3. --- ASSEMBLE AND RETURN THE CREW ---
        
        return Crew(
            agents=[launch_strategist, execution_coordinator, post_launch_analyst],
            tasks=[task_launch_preparation, task_launch_execution, task_post_launch_analysis],
            process=Process.sequential,
            verbose=True
        )
=======
import asyncio
from typing import Dict, List, Optional, Any
from crewai import Crew, Process, Task
from pydantic import BaseModel, Field

from ..agents.launch_agent import LaunchAgent
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

    def _create_crew(self) -> Crew:
        """Create the Launch Crew with agents and tasks."""
        agents = [
            self.launch_agent(name="Launch Preparer", role="Launch preparation expert"),
            self.launch_agent(name="Execution Coordinator", role="Launch day coordinator"),
            self.launch_agent(name="Post-Launch Analyst", role="Post-launch analysis specialist"),
            self.launch_agent(name="Crisis Manager", role="Crisis management expert"),
            self.launch_agent(name="Momentum Builder", role="Momentum sustaining strategist"),
        ]

        tasks = [
            Task(
                description="""
                Prepare comprehensive launch strategy and execution checklist.
                Prepare: 1. Launch timeline, 2. Pre-launch marketing,
                3. Technical readiness, 4. Team coordination, 5. Crisis planning.
                Provide launch preparation.
                """,
                agent=agents[0],
                expected_output="Comprehensive launch preparation with checklist."
            ),
            Task(
                description="""
                Execute launch day activities and coordinate efforts.
                Execute: 1. Timeline execution, 2. Real-time monitoring,
                3. Team coordination, 4. Customer support, 5. Performance optimization.
                Provide execution report.
                """,
                agent=agents[1],
                expected_output="Launch day execution report with metrics.",
                context=[tasks[0]]
            ),
            Task(
                description="""
                Analyze launch performance and gather insights.
                Analyze: 1. Performance metrics, 2. User acquisition,
                3. Technical stability, 4. Customer feedback, 5. Market response.
                Provide analysis.
                """,
                agent=agents[2],
                expected_output="Comprehensive post-launch analysis.",
                context=[tasks[1]]
            ),
            Task(
                description="""
                Plan crisis management and issue resolution strategies.
                Plan: 1. Crisis scenarios, 2. Communication protocols,
                3. Escalation procedures, 4. Recovery strategies, 5. Learning processes.
                Provide framework.
                """,
                agent=agents[3],
                expected_output="Crisis management framework.",
                context=[tasks[0]]
            ),
            Task(
                description="""
                Develop strategies to sustain launch momentum.
                Develop: 1. Post-launch marketing, 2. User retention,
                3. Feature planning, 4. Community building, 5. Success metrics.
                Provide strategy.
                """,
                agent=agents[4],
                expected_output="Momentum sustaining strategy with roadmap.",
                context=[tasks[2], tasks[3]]
            ),
        ]

        return Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
        )

    async def prepare_launch(self, product_info: Dict[str, Any], launch_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        project_data = self.project_data.copy()
        project_data.update({"product_info": product_info, "launch_context": launch_context})
        result = await self.run_async(project_data)
        return result.get("launch", {})

    async def execute_launch(self, launch_plan: Dict[str, Any]) -> Dict[str, Any]:
        project_data = self.project_data.copy()
        project_data.update({"launch_plan": launch_plan})
        result = await self.run_async(project_data)
        return result.get("launch", {})

    async def analyze_launch_performance(self, launch_data: Dict[str, Any]) -> Dict[str, Any]:
        project_data = self.project_data.copy()
        project_data.update({"launch_data": launch_data})
        result = await self.run_async(project_data)
        return result.get("launch", {})
>>>>>>> Stashed changes
