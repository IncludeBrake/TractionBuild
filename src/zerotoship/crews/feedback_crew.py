from crewai import Crew, Agent, Task, Process
from .base_crew import BaseCrew # Import our standardized base class

class FeedbackCrew(BaseCrew):
    """
    The FeedbackCrew is a specialized team of AI agents that serves as the final
    quality gate. It assesses all project outputs, gathers feedback, and
    generates an actionable roadmap for continuous improvement.
    """

    def _create_crew(self) -> Crew:
        """
        Defines the agents and tasks that form the FeedbackCrew.
        """

        # 1. --- DEFINE SPECIALIZED AGENTS ---

        quality_assessor = Agent(
            role="Lead Quality Assurance Engineer",
            goal="Rigorously assess all project deliverables against functional requirements, performance benchmarks, and security standards.",
            backstory="You are a meticulous QA engineer with a passion for quality. You systematically review code, documentation, and marketing assets to ensure they meet the highest standards of excellence.",
            tools=[],
            allow_delegation=False,
            verbose=True
        )

        feedback_collector = Agent(
            role="User Experience (UX) Researcher",
            goal="Synthesize all available feedback from stakeholders, potential users, and market response to identify key themes and sentiment.",
            backstory="You are an expert in qualitative and quantitative data analysis. You can distill vast amounts of feedback into clear, actionable insights about user satisfaction and stakeholder expectations.",
            tools=[], # e.g., SentimentAnalysisTool
            allow_delegation=False,
            verbose=True
        )

        improvement_analyst = Agent(
            role="Continuous Improvement Strategist",
            goal="Analyze quality reports and feedback insights to identify and prioritize the most impactful improvement opportunities for the project.",
            backstory="You are a strategic thinker who connects quality issues and user feedback to business outcomes. You excel at creating prioritized roadmaps that focus on changes that will deliver the most value.",
            tools=[],
            allow_delegation=False,
            verbose=True
        )
        
        # 2. --- DEFINE THE SEQUENTIAL TASKS ---

        task_quality_assessment = Task(
            description="Conduct a comprehensive quality assessment of the entire project_data object. Review the outputs from the Validator, "
                        "Execution, Builder, and Marketing crews. Assess code quality, documentation, test coverage, and marketing asset quality.",
            expected_output="A detailed quality assessment report, scoring each project area and highlighting any deviations from best practices.",
            agent=quality_assessor
        )
        
        task_feedback_collection = Task(
            description="Synthesize all feedback-related information within the project_data. Analyze market response, stakeholder expectations, "
                        "and potential user sentiment to create a unified feedback summary.",
            expected_output="A structured feedback analysis report identifying key themes, satisfaction metrics, and stakeholder requirements.",
            agent=feedback_collector,
            context=[task_quality_assessment] # Depends on the initial QA check
        )

        task_improvement_analysis = Task(
            description="Based on the Quality Assessment Report and the Feedback Analysis Report, identify and prioritize a list of improvement opportunities. "
                        "For each opportunity, assess its potential impact, implementation feasibility, and required resources.",
            expected_output="A prioritized improvement roadmap, with each item clearly detailed with impact and feasibility scores.",
            agent=improvement_analyst,
            context=[task_quality_assessment, task_feedback_collection] # Uses both previous reports
        )

        # 3. --- ASSEMBLE AND RETURN THE CREW ---

        return Crew(
            agents=[quality_assessor, feedback_collector, improvement_analyst],
            tasks=[task_quality_assessment, task_feedback_collection, task_improvement_analysis],
            process=Process.sequential,
            verbose=True
        )