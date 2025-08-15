"""
Marketing Crew for ZeroToShip.
Orchestrates launch preparation, positioning, and marketing strategy.
"""

import asyncio
from typing import Dict, List, Optional, Any
from crewai import Crew, Process, Task
from pydantic import BaseModel, Field

from .base_crew import BaseCrew
from ..agents.marketing_agent import MarketingAgent
from ..tools.market_tools import MarketTools
from ..tools.market_oracle_tool import MarketOracleTool
from ..tools.x_semantic_search_tool import XSemanticSearchTool
from ..tools.celery_execution_tool import CeleryExecutionTool
from ..core.project_meta_memory import ProjectMetaMemoryManager
from ..utils.llm_factory import get_llm

class MarketingCrewConfig(BaseModel):
    """Configuration for the Marketing Crew."""
    enable_memory_learning: bool = Field(default=True, description="Enable memory learning")
    enable_positioning: bool = Field(default=True, description="Enable market positioning")
    max_marketing_iterations: int = Field(default=3, description="Maximum marketing iterations")
    enable_asset_generation: bool = Field(default=True, description="Enable marketing asset generation")
    enable_launch_strategy: bool = Field(default=True, description="Enable launch strategy development")

class MarketingCrew(BaseCrew):
    """Marketing Crew for comprehensive launch preparation and positioning."""
    
    def __init__(self, project_data: Dict[str, Any]):
        super().__init__(project_data)
        self.memory_manager = ProjectMetaMemoryManager()
        self.marketing_agent = MarketingAgent()
        self.celery_executor = CeleryExecutionTool()

    def _create_crew(self) -> Crew:
        """Create the Marketing Crew with agents and tasks."""
        context = self.get_project_context()
        # Get LLM from the factory
        llm = get_llm()
        
        agents = [
            self.marketing_agent(name="Positioning Specialist", role="Market positioning expert", tools=[MarketOracleTool(), XSemanticSearchTool()], llm=llm),
            self.marketing_agent(name="Content Creator", role="Marketing content creator", llm=llm),
            self.marketing_agent(name="Channel Strategist", role="Distribution channel planner", llm=llm),
            self.marketing_agent(name="Launch Planner", role="Launch strategy developer", llm=llm),
            self.marketing_agent(name="Performance Analyst", role="Performance optimization expert", llm=llm),
        ]

        # Create tasks separately to avoid forward references
        task1 = Task(
            description=f"""
            Develop comprehensive market positioning strategy for the product.
            Focus on: 1. Target audience, 2. Competitive positioning,
            3. Value proposition, 4. Brand messaging, 5. Market entry strategy.
            Use real-time market data.
            Project Context: {context}
            Provide positioning framework.
            """,
            agent=agents[0],
            expected_output="Comprehensive market positioning strategy with messaging framework."
        )
        
        task2 = Task(
            description=f"""
            Generate comprehensive marketing assets and content.
            Create: 1. Website copy, 2. Social media content,
            3. Email sequences, 4. Press releases, 5. Sales collateral.
            Project Context: {context}
            Provide marketing materials.
            """,
            agent=agents[1],
            expected_output="Complete marketing asset suite with content.",
            context=[task1]
        )
        
        task3 = Task(
            description=f"""
            Plan comprehensive distribution channel strategy.
            Plan: 1. Distribution channels, 2. Channel messaging,
            3. Partnerships, 4. Digital mix, 5. Offline opportunities.
            Project Context: {context}
            Provide channel strategy.
            """,
            agent=agents[2],
            expected_output="Comprehensive distribution channel strategy with roadmap.",
            context=[task2]
        )
        
        task4 = Task(
            description=f"""
            Develop comprehensive launch strategy and timeline.
            Develop: 1. Launch timeline, 2. Pre-launch buzz,
            3. Launch day plan, 4. Post-launch, 5. Crisis plans.
            Project Context: {context}
            Provide launch strategy.
            """,
            agent=agents[3],
            expected_output="Comprehensive launch strategy with timeline.",
            context=[task3]
        )
        
        task5 = Task(
            description=f"""
            Plan comprehensive performance tracking and optimization.
            Plan: 1. KPIs, 2. Analytics, 3. A/B testing,
            4. Conversion optimization, 5. ROI measurement.
            Project Context: {context}
            Provide optimization framework.
            """,
            agent=agents[4],
            expected_output="Comprehensive performance optimization plan with tracking.",
            context=[task4]
        )
        
        tasks = [task1, task2, task3, task4, task5]

        return Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
        )

    async def _execute_crew(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the Marketing Crew using distributed execution."""
        task_type = next(iter(inputs.keys()), "create_positioning")
        task_result = await self.celery_executor.execute_task(
            lambda: self.crew.kickoff_async(inputs=inputs)
        )
        result = task_result.result() if task_result else {}
        return result.get(task_type, {})

    async def create_positioning(self, product_spec: Dict[str, Any], market_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        project_data = self.project_data.copy()
        project_data.update({"product_spec": product_spec, "market_data": market_data})
        return await self._execute_crew(project_data)

    async def generate_marketing_assets(self, positioning: Dict[str, Any], asset_requirements: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        project_data = self.project_data.copy()
        project_data.update({"positioning": positioning, "asset_requirements": asset_requirements})
        return await self._execute_crew(project_data)

    async def create_launch_strategy(self, product_info: Dict[str, Any], market_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        project_data = self.project_data.copy()
        project_data.update({"product_info": product_info, "market_context": market_context})
        return await self._execute_crew(project_data)