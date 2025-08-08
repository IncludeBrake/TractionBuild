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
        """Initialize the Feedback Crew with project data."""
        self.memory_manager = ProjectMetaMemoryManager()
        self.feedback_agent = FeedbackAgent()
        super().__init__(project_data)
        
    def _create_crew(self) -> Crew:
        """Create the CrewAI crew for feedback tasks."""
        # Get project context
        context = self.get_project_context()
        
        # Create agents
        quality_assessor = FeedbackAgent()()
        feedback_collector = FeedbackAgent()()
        improvement_analyst = FeedbackAgent()()
        validation_specialist = FeedbackAgent()()
        continuous_improvement_coordinator = FeedbackAgent()()
        
        # Create tasks
        tasks = []
        
        # Task 1: Comprehensive Quality Assessment
        tasks.append(Task(
            description=f"""
            Conduct comprehensive quality assessment of all project deliverables.
            
            Assess:
            1. Code quality and best practices compliance
            2. Documentation completeness and accuracy
            3. Test coverage and reliability
            4. Performance and scalability metrics
            5. Security and compliance requirements
            
            Project Context: {context}
            
            Provide detailed quality assessment with improvement recommendations.
            """,
            agent=quality_assessor,
            expected_output="Comprehensive quality assessment report with actionable recommendations."
        ))
        
        # Task 2: Stakeholder Feedback Collection
        tasks.append(Task(
            description=f"""
            Collect comprehensive feedback from all project stakeholders.
            
            Collect:
            1. User feedback and satisfaction metrics
            2. Stakeholder expectations and requirements
            3. Team feedback and process improvements
            4. External reviewer feedback
            5. Market response and validation
            
            Project Context: {context}
            
            Provide structured feedback analysis with priority recommendations.
            """,
            agent=feedback_collector,
            expected_output="Comprehensive feedback analysis with stakeholder insights."
        ))
        
        # Task 3: Improvement Opportunity Analysis
        tasks.append(Task(
            description=f"""
            Analyze collected feedback and identify improvement opportunities.
            
            Analyze:
            1. Feedback patterns and recurring themes
            2. Priority improvement areas
            3. Resource allocation for improvements
            4. Impact assessment of proposed changes
            5. Implementation feasibility and timeline
            
            Project Context: {context}
            
            Provide prioritized improvement roadmap with impact analysis.
            """,
            agent=improvement_analyst,
            expected_output="Prioritized improvement roadmap with implementation plan."
        ))
        
        # Task 4: Output Validation and Verification
        tasks.append(Task(
            description=f"""
            Validate and verify all outputs against project requirements.
            
            Validate:
            1. Functional requirements compliance
            2. Non-functional requirements verification
            3. Quality standards adherence
            4. Performance benchmarks achievement
            5. Security and compliance validation
            
            Project Context: {context}
            
            Provide validation report with verification results.
            """,
            agent=validation_specialist,
            expected_output="Comprehensive validation report with verification results."
        ))
        
        # Task 5: Continuous Improvement Implementation
        tasks.append(Task(
            description=f"""
            Implement continuous improvement recommendations and optimizations.
            
            Implement:
            1. High-priority improvement recommendations
            2. Process optimizations and workflow improvements
            3. Quality enhancement measures
            4. Performance optimizations
            5. Documentation and training improvements
            
            Project Context: {context}
            
            Provide implementation report with measurable improvements.
            """,
            agent=continuous_improvement_coordinator,
            expected_output="Continuous improvement implementation report with metrics."
        ))
        
        # Create and return the crew
        return Crew(
            agents=[
                quality_assessor,
                feedback_collector,
                improvement_analyst,
                validation_specialist,
                continuous_improvement_coordinator
            ],
            tasks=tasks,
            process=Process.sequential,
            verbose=True
        )



    async def validate_output(self, output: Dict[str, Any], requirements: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate output against requirements and quality standards.
        
        Args:
            output: Output to validate
            requirements: Requirements and quality standards
            
        Returns:
            Validation results and recommendations
        """
        # Store validation request in memory
        self.memory_manager.add_success_pattern(
            pattern={"validation_request": {"output": output, "requirements": requirements}},
            project_id="feedback_crew",
            agent_id="feedback_crew",
            confidence_score=0.8
        )
        
        # Execute the crew workflow
        inputs = {
            "output": output,
            "requirements": requirements or {},
            "validation_steps": [
                "comprehensive_quality_assessment",
                "stakeholder_feedback_collection",
                "improvement_opportunity_analysis",
                "output_validation_and_verification",
                "continuous_improvement_implementation"
            ]
        }
        
        result = await self.crew().kickoff(inputs=inputs)
        
        # Store validation result in memory
        self.memory_manager.add_success_pattern(
            pattern={"validation_result": result},
            project_id="feedback_crew",
            agent_id="feedback_crew",
            confidence_score=0.9
        )
        
        return {
            "validation_status": result.get("validation_status", "pending"),
            "quality_score": result.get("quality_score", 0.0),
            "issues_found": result.get("issues_found", []),
            "improvement_recommendations": result.get("improvement_recommendations", []),
            "compliance_status": result.get("compliance_status", {}),
            "performance_metrics": result.get("performance_metrics", {})
        }

    async def collect_feedback(self, project_data: Dict[str, Any], feedback_sources: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Collect comprehensive feedback from multiple sources.
        
        Args:
            project_data: Project data and deliverables
            feedback_sources: Sources to collect feedback from
            
        Returns:
            Collected feedback and analysis
        """
        # Store feedback collection in memory
        self.memory_manager.add_success_pattern(
            pattern={"feedback_collection": {"project_data": project_data, "sources": feedback_sources}},
            project_id="feedback_crew",
            agent_id="feedback_crew",
            confidence_score=0.8
        )
        
        # Execute feedback collection
        inputs = {
            "project_data": project_data,
            "feedback_sources": feedback_sources or ["users", "stakeholders", "team", "reviewers"],
            "collection_type": "comprehensive_feedback"
        }
        
        result = await self.crew().kickoff(inputs=inputs)
        
        return {
            "user_feedback": result.get("user_feedback", {}),
            "stakeholder_feedback": result.get("stakeholder_feedback", {}),
            "team_feedback": result.get("team_feedback", {}),
            "external_feedback": result.get("external_feedback", {}),
            "feedback_analysis": result.get("feedback_analysis", {}),
            "priority_recommendations": result.get("priority_recommendations", [])
        }

    async def generate_quality_report(self, project_results: Dict[str, Any], quality_metrics: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate comprehensive quality assurance report.
        
        Args:
            project_results: Project results and deliverables
            quality_metrics: Quality metrics and benchmarks
            
        Returns:
            Comprehensive quality report
        """
        # Store quality report generation in memory
        self.memory_manager.add_success_pattern(
            pattern={"quality_report": {"project_results": project_results, "metrics": quality_metrics}},
            project_id="feedback_crew",
            agent_id="feedback_crew",
            confidence_score=0.8
        )
        
        # Execute quality report generation
        inputs = {
            "project_results": project_results,
            "quality_metrics": quality_metrics or {},
            "report_type": "comprehensive_quality"
        }
        
        result = await self.crew().kickoff(inputs=inputs)
        
        return {
            "quality_summary": result.get("quality_summary", {}),
            "detailed_analysis": result.get("detailed_analysis", {}),
            "improvement_areas": result.get("improvement_areas", []),
            "success_metrics": result.get("success_metrics", {}),
            "recommendations": result.get("recommendations", []),
            "next_steps": result.get("next_steps", [])
        }

 