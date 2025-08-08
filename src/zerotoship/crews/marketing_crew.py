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
        """Initialize the Marketing Crew with project data."""
        self.memory_manager = ProjectMetaMemoryManager()
        self.marketing_agent = MarketingAgent()
        super().__init__(project_data)
        
    def _create_crew(self) -> Crew:
        """Create the CrewAI crew for marketing tasks."""
        # Get project context
        context = self.get_project_context()
        
        # Create agents
        positioning_specialist = MarketingAgent()()
        content_creator = MarketingAgent()()
        channel_strategist = MarketingAgent()()
        launch_planner = MarketingAgent()()
        performance_analyst = MarketingAgent()()

        # Create tasks
        tasks = []
        
        # Task 1: Market Positioning Strategy
        tasks.append(Task(
            description=f"""
            Develop comprehensive market positioning strategy for the product.
            
            Focus on:
            1. Target audience identification and segmentation
            2. Competitive positioning and differentiation
            3. Value proposition development
            4. Brand messaging and voice
            5. Market entry positioning strategy
            
            Project Context: {context}
            
            Provide detailed positioning framework with messaging guidelines.
            """,
            agent=positioning_specialist,
            expected_output="Comprehensive market positioning strategy with messaging framework."
        ))

        # Task 2: Marketing Asset Generation
        tasks.append(Task(
            description=f"""
            Generate comprehensive marketing assets and content.
            
            Create:
            1. Website copy and landing pages
            2. Social media content and campaigns
            3. Email marketing sequences
            4. Press releases and media kits
            5. Sales collateral and presentations
            
            Project Context: {context}
            
            Provide high-quality, conversion-optimized marketing materials.
            """,
            agent=content_creator,
            expected_output="Complete marketing asset suite with conversion-optimized content."
        ))

        # Task 3: Distribution Channel Planning
        tasks.append(Task(
            description=f"""
            Plan comprehensive distribution channel strategy.
            
            Plan:
            1. Primary and secondary distribution channels
            2. Channel-specific messaging and positioning
            3. Partnership and affiliate strategies
            4. Digital marketing channel mix
            5. Offline and event marketing opportunities
            
            Project Context: {context}
            
            Provide detailed channel strategy with implementation roadmap.
            """,
            agent=channel_strategist,
            expected_output="Comprehensive distribution channel strategy with implementation plan."
        ))

        # Task 4: Launch Strategy Development
        tasks.append(Task(
            description=f"""
            Develop comprehensive launch strategy and timeline.
            
            Develop:
            1. Launch timeline and milestone planning
            2. Pre-launch buzz and anticipation building
            3. Launch day execution plan
            4. Post-launch momentum strategies
            5. Crisis management and contingency plans
            
            Project Context: {context}
            
            Provide detailed launch strategy with execution timeline.
            """,
            agent=launch_planner,
            expected_output="Comprehensive launch strategy with execution timeline and contingencies."
        ))

        # Task 5: Performance Optimization Planning
        tasks.append(Task(
            description=f"""
            Plan comprehensive performance tracking and optimization.
            
            Plan:
            1. Key performance indicators (KPIs) and metrics
            2. Analytics and tracking implementation
            3. A/B testing and optimization strategies
            4. Conversion rate optimization (CRO) plans
            5. ROI measurement and attribution modeling
            
            Project Context: {context}
            
            Provide comprehensive performance optimization framework.
            """,
            agent=performance_analyst,
            expected_output="Comprehensive performance optimization plan with tracking framework."
        ))
        
        # Create and return the crew
        return Crew(
            agents=[
                positioning_specialist,
                content_creator,
                channel_strategist,
                launch_planner,
                performance_analyst
            ],
            tasks=tasks,
            process=Process.sequential,
            verbose=True
        )

    async def create_positioning(self, product_spec: Dict[str, Any], market_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create market positioning strategy for the product.
        
        Args:
            product_spec: Product specification and features
            market_data: Market research and competitive data
            
        Returns:
            Comprehensive positioning strategy
        """
        # Store positioning request in memory
        self.memory_manager.add_success_pattern(
            pattern={"positioning_request": {"product_spec": product_spec, "market_data": market_data}},
            project_id="marketing_crew",
            agent_id="marketing_crew",
            confidence_score=0.8
        )
        
        # Execute the crew workflow
        inputs = {
            "product_spec": product_spec,
            "market_data": market_data or {},
            "positioning_steps": [
                "market_positioning_strategy",
                "marketing_asset_generation",
                "distribution_channel_planning",
                "launch_strategy_development",
                "performance_optimization_planning"
            ]
        }
        
        result = await self.crew().kickoff(inputs=inputs)
        
        # Store positioning result in memory
        self.memory_manager.add_success_pattern(
            pattern={"positioning_result": result},
            project_id="marketing_crew",
            agent_id="marketing_crew",
            confidence_score=0.9
        )
        
        return {
            "positioning_strategy": result.get("positioning_strategy", {}),
            "target_audience": result.get("target_audience", {}),
            "value_proposition": result.get("value_proposition", ""),
            "messaging_framework": result.get("messaging_framework", {}),
            "competitive_analysis": result.get("competitive_analysis", {}),
            "brand_guidelines": result.get("brand_guidelines", {})
        }

    async def generate_marketing_assets(self, positioning: Dict[str, Any], asset_requirements: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate comprehensive marketing assets based on positioning.
        
        Args:
            positioning: Market positioning strategy
            asset_requirements: Specific asset requirements
            
        Returns:
            Generated marketing assets and content
        """
        # Store asset generation in memory
        self.memory_manager.add_success_pattern(
            pattern={"asset_generation": {"positioning": positioning, "requirements": asset_requirements}},
            project_id="marketing_crew",
            agent_id="marketing_crew",
            confidence_score=0.8
        )
        
        # Execute asset generation
        inputs = {
            "positioning": positioning,
            "asset_requirements": asset_requirements or {},
            "generation_type": "marketing_assets"
        }
        
        result = await self.crew().kickoff(inputs=inputs)
        
        return {
            "website_copy": result.get("website_copy", {}),
            "social_media_content": result.get("social_media_content", []),
            "email_sequences": result.get("email_sequences", []),
            "press_materials": result.get("press_materials", {}),
            "sales_collateral": result.get("sales_collateral", {}),
            "advertising_copy": result.get("advertising_copy", {})
        }

    async def create_launch_strategy(self, product_info: Dict[str, Any], market_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create comprehensive launch strategy for the product.
        
        Args:
            product_info: Product information and features
            market_context: Market context and timing considerations
            
        Returns:
            Comprehensive launch strategy
        """
        # Store launch strategy in memory
        self.memory_manager.add_success_pattern(
            pattern={"launch_strategy": {"product_info": product_info, "market_context": market_context}},
            project_id="marketing_crew",
            agent_id="marketing_crew",
            confidence_score=0.8
        )
        
        # Execute launch strategy creation
        inputs = {
            "product_info": product_info,
            "market_context": market_context or {},
            "strategy_type": "launch_planning"
        }
        
        result = await self.crew().kickoff(inputs=inputs)
        
        return {
            "launch_timeline": result.get("launch_timeline", {}),
            "pre_launch_activities": result.get("pre_launch_activities", []),
            "launch_day_plan": result.get("launch_day_plan", {}),
            "post_launch_strategy": result.get("post_launch_strategy", {}),
            "crisis_management": result.get("crisis_management", {}),
            "success_metrics": result.get("success_metrics", [])
        }

 