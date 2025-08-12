from crewai import Crew, Agent, Task, Process
from .base_crew import BaseCrew # Import our standardized base class

class ValidatorCrew(BaseCrew):
    """
    The ValidatorCrew is the first gate in the ZeroToShip pipeline. It is a
    specialized team of AI agents that conducts comprehensive market research,
    competitor analysis, and risk assessment to validate a business idea.
    """

    def _create_crew(self) -> Crew:
        """
        Defines the agents and tasks that form the ValidatorCrew.
        """
        idea = self.project_data.get("idea", "[No idea provided]")

        # 1. --- DEFINE SPECIALIZED AGENTS ---

        market_researcher = Agent(
            role="Senior Market Research Analyst",
            goal=f"Conduct in-depth market research for the idea: '{idea}'. Analyze market size, trends, and target audience.",
            backstory="You are a meticulous market analyst with 15 years of experience at a top-tier consulting firm. You excel at uncovering data-driven insights and identifying untapped market opportunities.",
            tools=[], # e.g., WebSearchTool, MarketDataAPITool
            allow_delegation=False,
            verbose=True
        )

        competitor_analyst = Agent(
            role="Competitive Intelligence Analyst",
            goal=f"Analyze the competitive landscape for the idea: '{idea}'. Identify key competitors, their strategies, and market positioning.",
            backstory="You are a strategic analyst who lives and breathes competitive intelligence. You can dissect any market to find strategic gaps and opportunities for differentiation.",
            tools=[], # e.g., ScrapeWebsiteTool
            allow_delegation=False,
            verbose=True
        )

        risk_assessor = Agent(
            role="Venture Capital Risk Assessor",
            goal=f"Evaluate all potential market, technical, and execution risks associated with the idea: '{idea}'.",
            backstory="You are a seasoned risk assessor from a leading VC firm. Your job is to poke holes in business ideas and identify every potential point of failure, providing clear mitigation strategies.",
            tools=[],
            allow_delegation=False,
            verbose=True
        )
        
        validation_synthesizer = Agent(
            role="Lead Validation Strategist",
            goal="Synthesize all research, competitive analysis, and risk assessments into a final, data-driven go/no-go recommendation.",
            backstory="You are the final decision-maker. Your role is to weigh all the evidence from your team of analysts and produce a clear, concise, and actionable recommendation with a quantifiable confidence score.",
            tools=[],
            allow_delegation=False,
            verbose=True
        )

        # 2. --- DEFINE THE SEQUENTIAL TASKS ---

        task_market_research = Task(
            description="Conduct comprehensive market research to understand the potential for the provided idea. "
                        "Focus on market size (TAM, SAM, SOM), key growth trends, and defining the primary target audience personas.",
            expected_output="A detailed market research report with quantified market size estimates and rich descriptions of the target audience.",
            agent=market_researcher
        )

        task_competitor_analysis = Task(
            description="Analyze the direct and indirect competitors. Identify their strengths, weaknesses, and market positioning. "
                        "Pinpoint any gaps in the market that our product could fill.",
            expected_output="A competitive analysis matrix and a summary of strategic opportunities for differentiation.",
            agent=competitor_analyst,
            context=[task_market_research]
        )

        task_risk_assessment = Task(
            description="Identify and evaluate potential risks across all domains: market (e.g., saturation), "
                        "technical (e.g., feasibility), and execution (e.g., resource needs). Propose clear mitigation strategies for the top 3 risks.",
            expected_output="A risk assessment report with a prioritized list of risks and actionable mitigation plans.",
            agent=risk_assessor,
            context=[task_market_research, task_competitor_analysis]
        )
        
        task_synthesis = Task(
            description="Synthesize the findings from the market research, competitive analysis, and risk assessment into a final report. "
                        "Conclude with a clear 'GO' or 'NO-GO' recommendation and a confidence score (0.0 to 1.0).",
            expected_output="A final validation report containing a summary of all findings, a clear recommendation, and a confidence score.",
            agent=validation_synthesizer,
            context=[task_market_research, task_competitor_analysis, task_risk_assessment]
        )
        
        # 3. --- ASSEMBLE AND RETURN THE CREW ---
        
        return Crew(
            agents=[market_researcher, competitor_analyst, risk_assessor, validation_synthesizer],
            tasks=[task_market_research, task_competitor_analysis, task_risk_assessment, task_synthesis],
            process=Process.sequential,
            verbose=True
        )