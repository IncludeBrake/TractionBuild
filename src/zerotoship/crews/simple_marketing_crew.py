"""
Simple Marketing Crew - Real AI Implementation
Uses CrewAI to generate marketing content and strategy.
"""

import logging
from typing import Dict, Any, List

try:
    from crewai import Agent, Task
    from .crewai_adapter import CrewAIAdapter
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    Agent = None
    Task = None
    CrewAIAdapter = None

logger = logging.getLogger(__name__)


class SimpleMarketingCrew(CrewAIAdapter):
    """
    Marketing crew that creates go-to-market strategy and content.
    Focuses on:
    - Market analysis
    - Target audience identification
    - Marketing message creation
    - Content strategy
    """

    def __init__(self, project_data: Dict[str, Any]):
        """Initialize the Marketing Crew."""
        if not CREWAI_AVAILABLE:
            raise ImportError("CrewAI not available")

        super().__init__(project_data)
        self.idea = project_data.get("idea", "Unknown product")

    def create_agents(self) -> List[Agent]:
        """Create the marketing agents."""

        # Market Researcher Agent
        market_researcher = Agent(
            role="Market Research Analyst",
            goal=f"Analyze the market opportunity for: {self.idea}",
            backstory=(
                "You are an experienced market researcher with expertise in identifying "
                "target audiences, market trends, and competitive landscapes. You excel "
                "at finding unique positioning opportunities for new products."
            ),
            verbose=True,
            allow_delegation=False
        )

        # Marketing Strategist Agent
        marketing_strategist = Agent(
            role="Marketing Strategist",
            goal=f"Create a compelling marketing strategy for: {self.idea}",
            backstory=(
                "You are a creative marketing strategist with a proven track record of "
                "launching successful products. You know how to craft compelling messages "
                "that resonate with target audiences and drive conversions."
            ),
            verbose=True,
            allow_delegation=False
        )

        # Content Creator Agent
        content_creator = Agent(
            role="Content Marketing Specialist",
            goal=f"Generate engaging marketing content for: {self.idea}",
            backstory=(
                "You are a talented content creator who specializes in writing copy that "
                "converts. You understand SEO, social media trends, and how to create "
                "content that engages and persuades audiences."
            ),
            verbose=True,
            allow_delegation=False
        )

        return [market_researcher, marketing_strategist, content_creator]

    def create_tasks(self, agents: List[Agent]) -> List[Task]:
        """Create the marketing tasks."""

        market_researcher, marketing_strategist, content_creator = agents

        # Task 1: Market Analysis
        market_analysis_task = Task(
            description=f"""
            Conduct a comprehensive market analysis for: {self.idea}

            Your analysis should include:
            1. Target audience demographics and psychographics
            2. Market size and growth potential
            3. Key competitors and their positioning
            4. Market gaps and opportunities
            5. Potential barriers to entry

            Provide specific, actionable insights that can guide the marketing strategy.
            """,
            agent=market_researcher,
            expected_output="A detailed market analysis report with target audience profiles and competitive insights"
        )

        # Task 2: Marketing Strategy
        marketing_strategy_task = Task(
            description=f"""
            Based on the market analysis, create a comprehensive marketing strategy for: {self.idea}

            Your strategy should include:
            1. Unique value proposition (UVP)
            2. Brand positioning statement
            3. Key marketing channels (prioritized)
            4. Marketing message framework
            5. Launch timeline and milestones
            6. Success metrics and KPIs

            Make the strategy practical and executable for a startup launch.
            """,
            agent=marketing_strategist,
            expected_output="A complete marketing strategy document with UVP, positioning, channels, and metrics"
        )

        # Task 3: Marketing Content
        content_creation_task = Task(
            description=f"""
            Create compelling marketing content for: {self.idea}

            Generate the following:
            1. Product tagline (10 words max)
            2. Elevator pitch (2-3 sentences)
            3. Website hero section copy (headline + subheadline + CTA)
            4. 3 social media post ideas
            5. Email subject lines for launch campaign (5 variations)
            6. Product description for landing page (150-200 words)

            Ensure all content is clear, compelling, and aligned with the marketing strategy.
            """,
            agent=content_creator,
            expected_output="A complete marketing content package including tagline, elevator pitch, website copy, and social content"
        )

        return [market_analysis_task, marketing_strategy_task, content_creation_task]

    def get_next_state(self) -> str:
        """Marketing leads to validation."""
        return "VALIDATION"
