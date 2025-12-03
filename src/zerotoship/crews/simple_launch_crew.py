"""
Simple Launch Crew - Real AI Implementation
Uses CrewAI to plan and execute product launches.
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


class SimpleLaunchCrew(CrewAIAdapter):
    """
    Launch crew that orchestrates product launches.
    Focuses on:
    - Launch planning
    - Distribution strategy
    - Community engagement
    - Success tracking
    """

    def __init__(self, project_data: Dict[str, Any]):
        """Initialize the Launch Crew."""
        if not CREWAI_AVAILABLE:
            raise ImportError("CrewAI not available")

        super().__init__(project_data)
        self.idea = project_data.get("idea", "Unknown product")

    def create_agents(self) -> List[Agent]:
        """Create the launch agents."""

        # Launch Manager Agent
        launch_manager = Agent(
            role="Launch Manager",
            goal=f"Plan and coordinate successful launch for: {self.idea}",
            backstory=(
                "You are an experienced launch manager who has successfully launched "
                "numerous products. You know how to coordinate teams, manage timelines, "
                "and ensure all pieces come together for a successful launch."
            ),
            verbose=True,
            allow_delegation=False
        )

        # Growth Hacker Agent
        growth_hacker = Agent(
            role="Growth Hacker",
            goal=f"Create viral growth strategy for: {self.idea}",
            backstory=(
                "You are a creative growth hacker who specializes in finding unconventional "
                "ways to acquire users and drive growth. You understand viral loops, "
                "referral programs, and how to create buzz around new products."
            ),
            verbose=True,
            allow_delegation=False
        )

        return [launch_manager, growth_hacker]

    def create_tasks(self, agents: List[Agent]) -> List[Task]:
        """Create the launch tasks."""

        launch_manager, growth_hacker = agents

        # Task 1: Launch Plan
        launch_plan_task = Task(
            description=f"""
            Create a comprehensive launch plan for: {self.idea}

            Your plan should include:
            1. Launch timeline (pre-launch, launch day, post-launch)
            2. Launch checklist (all items that need to be completed)
            3. Distribution channels (where to announce/promote)
            4. Press and media strategy
            5. Influencer outreach plan
            6. Community engagement strategy
            7. Launch day schedule (hour-by-hour)
            8. Risk mitigation plan

            Make the plan actionable and realistic for a startup launch.
            """,
            agent=launch_manager,
            expected_output="Complete launch plan with timeline, checklist, and distribution strategy"
        )

        # Task 2: Growth Strategy
        growth_strategy_task = Task(
            description=f"""
            Create a viral growth strategy for: {self.idea}

            Your strategy should include:
            1. Viral loop design (how users will bring more users)
            2. Referral program mechanics
            3. Launch platforms to target (Product Hunt, Hacker News, etc.)
            4. Early adopter acquisition tactics
            5. Content marketing for launch
            6. Social media amplification strategy
            7. Partnership and collaboration opportunities
            8. First 100/1000/10000 user milestones

            Focus on creative, low-cost tactics that drive rapid growth.
            """,
            agent=growth_hacker,
            expected_output="Viral growth strategy with referral mechanics and acquisition tactics"
        )

        return [launch_plan_task, growth_strategy_task]

    def get_next_state(self) -> str:
        """Launch leads to completion."""
        return "COMPLETED"
