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
from ..core.project_meta_memory import ProjectMetaMemoryManager

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

    def _create_crew(self) -> Crew:
        """Create the Marketing Crew with agents and tasks."""
        context = self.get_project_context()
        agents = [
            self.marketing_agent(name="Positioning Specialist", role="Market positioning expert"),
            self.marketing_agent(name="Content Creator", role="Marketing content creator"),
            self.marketing_agent(name="Channel Strategist", role="Distribution channel planner"),
            self.marketing_agent(name="Launch Planner", role="Launch strategy developer"),
            self.marketing_agent(name="Performance Analyst", role="Performance optimization expert"),
        ]

        tasks = [
            Task(
                description=f"""
                Develop comprehensive market positioning strategy for the product.
                Focus on: 1. Target audience, 2. Competitive positioning,
                3. Value proposition, 4. Brand messaging, 5. Market entry strategy.
                Project Context: {context}
                Provide positioning framework.
                """,
                agent=agents[0],
                expected_output="Comprehensive market positioning strategy with messaging framework."
            ),
            Task(
                description=f"""
                Generate comprehensive marketing assets and content.
                Create: 1. Website copy, 2. Social media content,
                3. Email sequences, 4. Press releases, 5. Sales collateral.
                Project Context: {context}
                Provide marketing materials.
                """,
                agent=agents[1],
                expected_output="Complete marketing asset suite with content."
            ),
            Task(
                description=f"""
                Plan comprehensive distribution channel strategy.
                Plan: 1. Distribution channels, 2. Channel messaging,
                3. Partnerships, 4. Digital mix, 5. Offline opportunities.
                Project Context: {context}
                Provide channel strategy.
                """,
                agent=agents[2],
                expected_output="Comprehensive distribution channel strategy with roadmap."
            ),
            Task(
                description=f"""
                Develop comprehensive launch strategy and timeline.
                Develop: 1. Launch timeline, 2. Pre-launch buzz,
                3. Launch day plan, 4. Post-launch, 5. Crisis plans.
                Project Context: {context}
                Provide launch strategy.
                """,
                agent=agents[3],
                expected_output="Comprehensive launch strategy with timeline."
            ),
            Task(
                description=f"""
                Plan comprehensive performance tracking and optimization.
                Plan: 1. KPIs, 2. Analytics, 3. A/B testing,
                4. Conversion optimization, 5. ROI measurement.
                Project Context: {context}
                Provide optimization framework.
                """,
                agent=agents[4],
                expected_output="Comprehensive performance optimization plan with tracking."
            ),
        ]

        return Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
        )

    async def create_positioning(self, product_spec: Dict[str, Any], market_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        project_data = self.project_data.copy()
        project_data.update({"product_spec": product_spec, "market_data": market_data})
        result = await self.run_async(project_data)
        return result.get("marketing", {})

    async def generate_marketing_assets(self, positioning: Dict[str, Any], asset_requirements: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        project_data = self.project_data.copy()
        project_data.update({"positioning": positioning, "asset_requirements": asset_requirements})
        result = await self.run_async(project_data)
        return result.get("marketing", {})

    async def create_launch_strategy(self, product_info: Dict[str, Any], market_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        project_data = self.project_data.copy()
        project_data.update({"product_info": product_info, "market_context": market_context})
        result = await self.run_async(project_data)
        return result.get("marketing", {})
