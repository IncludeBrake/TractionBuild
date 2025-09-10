"""
Feedback Crew for tractionbuild.
Orchestrates quality assurance, feedback collection, and continuous improvement.
"""

import asyncio
from typing import Dict, List, Optional, Any
from crewai import Crew, Process, Task
from pydantic import BaseModel, Field

from .base_crew import BaseCrew
from ..agents.feedback_agent import FeedbackAgent
from ..tools.compliance_tool import ComplianceCheckerTool
from ..tools.celery_execution_tool import CeleryExecutionTool
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
        self.celery_executor = CeleryExecutionTool()

    def _create_crew(self) -> Crew:
        """Create the Feedback Crew with agents and tasks."""
        context = self.get_project_context()
        agents = [
            self.feedback_agent(name="Quality Assessor", role="Quality assessment expert", tools=[ComplianceCheckerTool()]),
            self.feedback_agent(name="Feedback Collector", role="Feedback collection specialist"),
            self.feedback_agent(name="Improvement Analyst", role="Improvement opportunity analyst"),
            self.feedback_agent(name="Validation Specialist", role="Output validation expert", tools=[ComplianceCheckerTool()]),
            self.feedback_agent(name="Continuous Improvement Coordinator", role="Improvement implementation coordinator"),
        ]

        # Create tasks separately to avoid forward references
        task1 = Task(
            description=f"""
            Conduct comprehensive quality assessment of all project deliverables.
            Assess: 1. Code quality, 2. Documentation, 3. Test coverage,
            4. Performance, 5. Security/compliance.
            Ensure GDPR compliance during assessment.
            Project Context: {context}
            Provide quality assessment.
            """,
            agent=agents[0],
            expected_output="Comprehensive quality assessment report."
        )
        
        task2 = Task(
            description=f"""
            Collect feedback from all project stakeholders.
            Collect: 1. User feedback, 2. Stakeholder expectations,
            3. Team feedback, 4. External reviews, 5. Market response.
            Project Context: {context}
            Provide feedback analysis.
            """,
            agent=agents[1],
            expected_output="Comprehensive feedback analysis.",
            context=[task1]
        )
        
        task3 = Task(
            description=f"""
            Analyze feedback and identify improvement opportunities.
            Analyze: 1. Patterns, 2. Priority areas, 3. Resource needs,
            4. Impact, 5. Feasibility.
            Project Context: {context}
            Provide improvement roadmap.
            """,
            agent=agents[2],
            expected_output="Prioritized improvement roadmap.",
            context=[task2]
        )
        
        task4 = Task(
            description=f"""
            Validate outputs against requirements.
            Validate: 1. Functional, 2. Non-functional, 3. Quality,
            4. Performance, 5. Security/compliance.
            Ensure GDPR compliance.
            Project Context: {context}
            Provide validation report.
            """,
            agent=agents[3],
            expected_output="Comprehensive validation report.",
            context=[task3]
        )
        
        task5 = Task(
            description=f"""
            Implement continuous improvement recommendations.
            Implement: 1. High-priority fixes, 2. Process optimizations,
            3. Quality measures, 4. Performance, 5. Documentation.
            Project Context: {context}
            Provide implementation report.
            """,
            agent=agents[4],
            expected_output="Continuous improvement implementation report.",
            context=[task4]
        )
        
        tasks = [task1, task2, task3, task4, task5]

        return Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
        )

    async def _execute_crew(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the Feedback Crew using distributed execution."""
        task_type = next(iter(inputs.keys()), "validate_output")
        # Execute crew directly instead of using Celery incorrectly
        result = await asyncio.to_thread(self.crew.kickoff, inputs=inputs)
        return result.get(task_type, {})

    async def validate_output(self, output: Dict[str, Any], requirements: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        project_data = self.project_data.copy()
        project_data.update({"output": output, "requirements": requirements})
        return await self._execute_crew(project_data)

    async def collect_feedback(self, project_data: Dict[str, Any], feedback_sources: Optional[List[str]] = None) -> Dict[str, Any]:
        project_data = self.project_data.copy()
        project_data.update({"project_data": project_data, "feedback_sources": feedback_sources})
        return await self._execute_crew(project_data)

    async def generate_quality_report(self, project_results: Dict[str, Any], quality_metrics: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        project_data = self.project_data.copy()
        project_data.update({"project_results": project_results, "quality_metrics": quality_metrics})
        return await self._execute_crew(project_data)