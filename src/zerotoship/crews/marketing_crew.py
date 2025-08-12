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