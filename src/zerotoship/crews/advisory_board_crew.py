from crewai import Crew, Agent, Task, Process
from .base_crew import BaseCrew
from ..tools.market_oracle_tool import MarketOracleTool

class AdvisoryBoardCrew(BaseCrew):
    """The Advisory Board crew that interactively refines a user's idea."""

    def _create_crew(self) -> Crew:
        # --- AGENT DEFINITIONS ---
        strategist = Agent(
            role='Chief Strategist & Orchestrator',
            goal='Lead the advisory board discussion to transform a vague user idea into a hyper-targeted, data-validated mission. Enforce ruthless clarity and prioritization.',
            backstory='You are a seasoned venture catalyst. Your job is to cut through fluff, ask probing questions, and synthesize the board\'s insights into an actionable plan.',
            verbose=True,
        )
        market_analyst = Agent(
            role='Real-Time Market Analyst',
            goal='Provide immediate, data-driven insights on the market landscape, trends, and audience sentiment using the Market Oracle.',
            backstory='You are a data wizard with access to live market feeds. You provide the objective data the board needs to make informed decisions.',
            verbose=True,
            tools=[MarketOracleTool()]
        )
        user_champion = Agent(
            role='User Champion & Empathy Advocate',
            goal='Ensure the refined idea deeply resonates with a specific user pain point. Advocate for the user and maintain a motivational, collaborative tone.',
            backstory='You are the voice of the customer. You challenge the board to think from a user-centric perspective and ensure the final mission is something people will actually want.',
            verbose=True,
        )
        # Add Tech Validator and Wild Card Innovator agents here as well...

        # --- TASK DEFINITION ---
        refinement_task = Task(
            description=f"Analyze and refine the user's initial idea: '{self.project_data['idea']}'. "
                        "Lead a discussion with the board. Use the Market Oracle to get real data. "
                        "Ask the user clarifying questions if needed. Your final goal is to produce a "
                        "single, hyper-targeted, and validated 'mission statement' for the project.",
            expected_output="A final, validated mission statement. Example: 'Build a meal planning app for vegan diabetic athletes who travel frequently'.",
            agent=strategist # The Strategist leads the crew
        )

        return Crew(
            agents=[strategist, market_analyst, user_champion], # Add other agents to this list
            tasks=[refinement_task],
            process=Process.sequential,
            verbose=True
        )