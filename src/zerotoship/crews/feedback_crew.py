<<<<<<< Updated upstream
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
=======
"""
Feedback Crew for ZeroToShip.
Orchestrates quality assurance, feedback collection, and continuous improvement.
"""

import asyncio
from typing import Dict, List, Optional, Any
from crewai import Crew, Process, Task
from pydantic import BaseModel, Field

from .base_crew import BaseCrew
from ..agents.feedback_agent import FeedbackAgent
from ..core.project_meta_memory import ProjectMetaMemoryManager

class FeedbackCrewConfig(BaseModel):
    """Configuration for the Feedback Crew."""
    enable_memory_learning: bool = Field(default=True, description="Enable memory learning")
    enable_quality_assurance: bool = Field(default=True, description="Enable quality assurance")
    max_feedback_iterations: int = Field(default=3, description="Maximum feedback iterations")
    enable_output_validation: bool = Field(default=True, description="Enable output validation")
    enable_continuous_improvement: bool = Field(default=True, description="Enable continuous improvement")

class FeedbackCrew(BaseCrew):
    """Feedback Crew for comprehensive quality assurance and feedback collection."""
    
    def __init__(self, project_data: Dict[str, Any]):
        super().__init__(project_data)
        self.memory_manager = ProjectMetaMemoryManager()
        self.feedback_agent = FeedbackAgent()

    def _create_crew(self) -> Crew:
        """Create the Feedback Crew with agents and tasks."""
        context = self.get_project_context()
        agents = [
            self.feedback_agent(name="Quality Assessor", role="Quality assessment expert"),
            self.feedback_agent(name="Feedback Collector", role="Feedback collection specialist"),
            self.feedback_agent(name="Improvement Analyst", role="Improvement opportunity analyst"),
            self.feedback_agent(name="Validation Specialist", role="Output validation expert"),
            self.feedback_agent(name="Continuous Improvement Coordinator", role="Improvement implementation coordinator"),
        ]

        tasks = [
            Task(
                description=f"""
                Conduct comprehensive quality assessment of all project deliverables.
                Assess: 1. Code quality, 2. Documentation, 3. Test coverage,
                4. Performance, 5. Security/compliance.
                Project Context: {context}
                Provide quality assessment.
                """,
                agent=agents[0],
                expected_output="Comprehensive quality assessment report."
            ),
            Task(
                description=f"""
                Collect feedback from all project stakeholders.
                Collect: 1. User feedback, 2. Stakeholder expectations,
                3. Team feedback, 4. External reviews, 5. Market response.
                Project Context: {context}
                Provide feedback analysis.
                """,
                agent=agents[1],
                expected_output="Comprehensive feedback analysis.",
                context=[tasks[0]]
            ),
            Task(
                description=f"""
                Analyze feedback and identify improvement opportunities.
                Analyze: 1. Patterns, 2. Priority areas, 3. Resource needs,
                4. Impact, 5. Feasibility.
                Project Context: {context}
                Provide improvement roadmap.
                """,
                agent=agents[2],
                expected_output="Prioritized improvement roadmap.",
                context=[tasks[1]]
            ),
            Task(
                description=f"""
                Validate outputs against requirements.
                Validate: 1. Functional, 2. Non-functional, 3. Quality,
                4. Performance, 5. Security/compliance.
                Project Context: {context}
                Provide validation report.
                """,
                agent=agents[3],
                expected_output="Comprehensive validation report.",
                context=[tasks[2]]
            ),
            Task(
                description=f"""
                Implement continuous improvement recommendations.
                Implement: 1. High-priority fixes, 2. Process optimizations,
                3. Quality measures, 4. Performance, 5. Documentation.
                Project Context: {context}
                Provide implementation report.
                """,
                agent=agents[4],
                expected_output="Continuous improvement implementation report.",
                context=[tasks[3]]
            ),
        ]

        return Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
        )

    async def validate_output(self, output: Dict[str, Any], requirements: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        project_data = self.project_data.copy()
        project_data.update({"output": output, "requirements": requirements})
        result = await self.run_async(project_data)
        return result.get("feedback", {})

    async def collect_feedback(self, project_data: Dict[str, Any], feedback_sources: Optional[List[str]] = None) -> Dict[str, Any]:
        project_data = self.project_data.copy()
        project_data.update({"project_data": project_data, "feedback_sources": feedback_sources})
        result = await self.run_async(project_data)
        return result.get("feedback", {})

    async def generate_quality_report(self, project_results: Dict[str, Any], quality_metrics: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        project_data = self.project_data.copy()
        project_data.update({"project_results": project_results, "quality_metrics": quality_metrics})
        result = await self.run_async(project_data)
        return result.get("feedback", {})
>>>>>>> Stashed changes
