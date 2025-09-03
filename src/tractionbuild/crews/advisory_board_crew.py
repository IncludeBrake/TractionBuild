"""
Advisory Board Crew for tractionbuild.
Orchestrates interactive idea refinement with market insights and user focus.
"""

import asyncio
from typing import Dict, Any, Optional
from crewai import Crew, Process, Task, Agent
from pydantic import BaseModel, Field

from .base_crew import BaseCrew
from ..tools.market_oracle_tool import MarketOracleTool
from ..tools.graph_context_tool import GraphContextTool
from ..core.project_meta_memory import ProjectMetaMemoryManager
from ..utils.llm_factory import get_llm

class AdvisoryBoardCrewConfig(BaseModel):
    """Configuration for the Advisory Board Crew."""
    enable_memory_learning: bool = Field(default=True, description="Enable memory learning")
    enable_interactive_refinement: bool = Field(default=True, description="Enable interactive idea refinement")
    max_refinement_iterations: int = Field(default=3, description="Maximum refinement iterations")

class AdvisoryBoardCrew(BaseCrew):
    """Advisory Board Crew that interactively refines a user's idea."""
    
    def __init__(self, project_data: Dict[str, Any], config: Optional[AdvisoryBoardCrewConfig] = None):
        """Initialize the Advisory Board Crew with project data and config."""
        super().__init__(project_data)
        self.config = config or AdvisoryBoardCrewConfig()
        self.memory_manager = ProjectMetaMemoryManager()

    def _create_crew(self) -> Crew:
        """Create the Advisory Board Crew with agents and tasks."""
        
        # Get LLM from the factory
        llm = get_llm()
        
        # Define specialized agents
        strategist = Agent(
            role="Chief Strategist & Orchestrator",
            goal="Lead the advisory board discussion to transform a vague user idea into a hyper-targeted, data-validated mission. Enforce ruthless clarity and prioritization.",
            backstory="You are a seasoned venture catalyst. Your job is to cut through fluff, ask probing questions, and synthesize the board's insights into an actionable plan.",
            verbose=True,
            tools=[GraphContextTool()],
            llm=llm
        )
        
        market_analyst = Agent(
            role="Real-Time Market Analyst",
            goal="Provide immediate, data-driven insights on the market landscape, trends, and audience sentiment using the Market Oracle.",
            backstory="You are a data wizard with access to live market feeds. You provide the objective data the board needs to make informed decisions.",
            verbose=True,
            tools=[MarketOracleTool()],
            llm=llm
        )
        
        user_champion = Agent(
            role="User Champion & Empathy Advocate",
            goal="Ensure the refined idea deeply resonates with a specific user pain point. Advocate for the user and maintain a motivational, collaborative tone.",
            backstory="You are the voice of the customer. You challenge the board to think from a user-centric perspective and ensure the final mission is desirable.",
            verbose=True,
            llm=llm
        )
        
        tech_validator = Agent(
            role="Tech Validator",
            goal="Validate the technical feasibility of the refined idea.",
            backstory="You are a tech expert ensuring the idea is technically viable.",
            verbose=True,
            llm=llm
        )
        
        wild_card_innovator = Agent(
            role="Wild Card Innovator",
            goal="Introduce creative, out-of-the-box enhancements to the idea.",
            backstory="You are a creative thinker pushing the boundaries of innovation.",
            verbose=True,
            llm=llm
        )

        # Define the refinement task
        context = self.get_project_context()
        idea = context.get("idea", "No idea provided")
        
        refinement_task = Task(
            description=f"""
            Analyze and refine the user's initial idea: '{idea}'.
            
            Lead a comprehensive discussion with the advisory board:
            1. Use the Market Oracle to get real-time data on market trends, competition, and user sentiment
            2. Ask clarifying questions to understand the core problem and target audience
            3. Evaluate technical feasibility and market opportunity
            4. Consider creative enhancements and differentiation strategies
            5. Synthesize all insights into a single, hyper-targeted mission statement
            
            Project Context: {context}
            
            Focus on creating a mission that is:
            - Specific and actionable
            - Data-validated with market insights
            - Technically feasible
            - User-centric and desirable
            - Differentiated from existing solutions
            """,
            expected_output="A final, validated mission statement with supporting rationale. Example: 'Build a meal planning app for vegan diabetic athletes who travel frequently'.",
            agent=strategist
        )

        return Crew(
            agents=[strategist, market_analyst, user_champion, tech_validator, wild_card_innovator],
            tasks=[refinement_task],
            process=Process.sequential,
            verbose=True,
        )

    async def _execute_crew(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the Advisory Board Crew to refine the idea."""
        idea = inputs.get("idea", self.project_data.get("idea", "No idea provided"))
        context = inputs.get("context", {})
        
        # Prepare inputs for the crew
        crew_inputs = {
            "idea": idea,
            "context": context,
            "project_data": self.project_data
        }
        
        result = await self.crew.kickoff_async(inputs=crew_inputs)
        
        # Process result into a structured output
        mission_statement = result.get("output", f"Refined mission for '{idea}' not fully defined")
        
        return {
            "mission_statement": mission_statement,
            "validation_status": "completed",
            "confidence_score": 0.8,  # Placeholder, could be derived from result
            "insights": result.get("insights", []),
            "recommendations": result.get("recommendations", []),
            "market_data": result.get("market_data", {}),
            "next_steps": [
                "Proceed to idea validation",
                "Begin market research",
                "Start technical planning"
            ]
        }
