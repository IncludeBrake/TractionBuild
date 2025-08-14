<<<<<<< Updated upstream
from crewai import Crew, Agent, Task, Process
from .base_crew import BaseCrew # Import our standardized base class

class MarketingCrew(BaseCrew):
    """
    The MarketingCrew is a specialized team of AI agents that develops a
    comprehensive go-to-market strategy, from brand positioning and messaging
    to content creation and channel planning.
    """

    def _create_crew(self) -> Crew:
        """
        Defines the agents and tasks that form the MarketingCrew.
        """

        # 1. --- DEFINE SPECIALIZED AGENTS ---

        brand_strategist = Agent(
            role="Chief Brand Strategist",
            goal="Develop a powerful market positioning and messaging framework that differentiates the product and resonates with the target audience.",
            backstory="You are a seasoned brand strategist who has crafted the narratives for iconic tech brands. You excel at finding a product's unique voice and creating a compelling value proposition.",
            tools=[],
            allow_delegation=False,
            verbose=True
        )

        content_creator = Agent(
            role="Lead Content Creator",
            goal="Generate a suite of high-quality, conversion-optimized marketing assets based on the brand strategy.",
            backstory="You are a versatile content creator and copywriter with a knack for producing engaging content across all formats, from landing pages to social media campaigns.",
            tools=[], # e.g., AIContentGenerator, ImageGenerationTool
            allow_delegation=False,
            verbose=True
        )

        channel_planner = Agent(
            role="Digital Marketing Channel Planner",
            goal="Identify the most effective distribution channels to reach the target audience and create a detailed channel strategy.",
            backstory="You are a data-driven marketing expert who understands the nuances of every digital channel. You can build an optimal marketing mix to maximize reach and ROI.",
            tools=[], # e.g., AudienceLocatorTool, SEOAnalyzerTool
            allow_delegation=False,
            verbose=True
        )

        # 2. --- DEFINE THE SEQUENTIAL TASKS ---

        task_positioning = Task(
            description="Based on the validated idea and target audience personas in the project data, develop a comprehensive market "
                        "positioning strategy. Define the unique value proposition, brand voice, and core messaging framework.",
            expected_output="A detailed brand positioning document that includes the value proposition, messaging guidelines, and competitive differentiation.",
            agent=brand_strategist
        )

        task_asset_generation = Task(
            description="Using the brand positioning document, generate a suite of essential marketing assets. This must include "
                        "website landing page copy, a sequence of 3 promotional emails, and 5 social media posts (3 for LinkedIn, 2 for X).",
            expected_output="A collection of text files containing the generated marketing assets.",
            agent=content_creator,
            context=[task_positioning] # Correctly references the Task object
        )
        
        task_channel_strategy = Task(
            description="Based on the target audience personas and brand positioning, create a detailed distribution channel plan. "
                        "Prioritize the top 3-4 channels and outline the specific content strategy for each.",
            expected_output="A channel strategy document detailing the marketing mix, channel-specific tactics, and key performance indicators (KPIs).",
            agent=channel_planner,
            context=[task_positioning]
        )
        
        # 3. --- ASSEMBLE AND RETURN THE CREW ---
        
        return Crew(
            agents=[brand_strategist, content_creator, channel_planner],
            tasks=[task_positioning, task_asset_generation, task_channel_strategy],
            process=Process.sequential,
            verbose=True
        )
=======
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
>>>>>>> Stashed changes
