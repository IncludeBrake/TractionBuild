"""
Feedback Agent for tractionbuild.
Handles quality assurance, feedback collection, and output validation.
"""

from typing import Dict, List, Optional, Any
from crewai import Agent
from pydantic import BaseModel, Field

from ..models.project import Project
from ..models.task import Task


class FeedbackAgentConfig(BaseModel):
    """Configuration for the Feedback Agent."""
    
    name: str = Field(default="Feedback Agent", description="Agent name")
    role: str = Field(default="Quality Assurance and Feedback", description="Agent role")
    goal: str = Field(
        default="Ensure quality outputs and collect actionable feedback",
        description="Agent goal"
    )
    backstory: str = Field(
        default="""You are an expert quality assurance specialist and user experience 
        researcher with 15+ years of experience in product testing, feedback analysis, 
        and quality control. You have helped improve hundreds of products through 
        systematic feedback collection and analysis.""",
        description="Agent backstory"
    )
    verbose: bool = Field(default=True, description="Enable verbose logging")
    allow_delegation: bool = Field(default=False, description="Allow task delegation")
    max_iterations: int = Field(default=3, description="Maximum iterations for feedback")


class FeedbackAgent:
    """Feedback Agent for quality assurance and feedback collection."""
    
    def __init__(self, config: Optional[FeedbackAgentConfig] = None):
        """Initialize the Feedback Agent."""
        self.config = config or FeedbackAgentConfig()
        self.agent = self._create_agent()
    
    def __call__(self) -> Agent:
        """Return the underlying CrewAI Agent for use in crews."""
        return self.agent
    
    def _create_agent(self) -> Agent:
        """Create the CrewAI agent instance."""
        return Agent(
            role=self.config.role,
            goal=self.config.goal,
            backstory=self.config.backstory,
            verbose=self.config.verbose,
            allow_delegation=self.config.allow_delegation,
            max_iter=self.config.max_iterations
        )
    
    async def validate_output(
        self, 
        output: str, 
        expected_format: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate agent output for quality and correctness.
        
        Args:
            output: Agent output to validate
            expected_format: Expected output format
            context: Additional context
            
        Returns:
            Validation results
        """
        # Simple validation logic
        issues = []
        confidence_score = 0.8
        
        # Check for common issues
        if not output or len(output.strip()) == 0:
            issues.append("Empty or missing output")
            confidence_score = 0.0
        elif len(output) < 10:
            issues.append("Output too short")
            confidence_score = 0.3
        elif "placeholder" in output.lower() or "tbd" in output.lower():
            issues.append("Contains placeholder content")
            confidence_score = 0.5
        
        # Check for security issues
        if "<script>" in output.lower():
            issues.append("Potential security issue: script tags")
            confidence_score = 0.2
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "confidence_score": confidence_score,
            "recommendations": [
                "Provide more detailed output",
                "Remove placeholder content",
                "Ensure proper formatting"
            ] if issues else ["Output looks good"]
        }
    
    async def collect_feedback(
        self, 
        project: Project, 
        deliverables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Collect feedback on project deliverables.
        
        Args:
            project: Project information
            deliverables: Project deliverables
            
        Returns:
            Feedback analysis
        """
        # Placeholder implementation
        return {
            "project_id": project.id,
            "feedback_score": 0.8,
            "strengths": [
                "Clear value proposition",
                "Good technical implementation",
                "User-friendly interface"
            ],
            "improvements": [
                "Add more documentation",
                "Improve error handling",
                "Enhance performance"
            ],
            "user_satisfaction": "high",
            "recommendations": [
                "Continue with current approach",
                "Focus on user experience improvements",
                "Consider additional features based on feedback"
            ]
        }
    
    async def generate_quality_report(
        self, 
        project: Project, 
        tasks: List[Task],
        outputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive quality report.
        
        Args:
            project: Project information
            tasks: List of completed tasks
            outputs: Project outputs
            
        Returns:
            Quality report
        """
        # Placeholder implementation
        return {
            "project_id": project.id,
            "overall_quality_score": 0.85,
            "code_quality": {
                "score": 0.9,
                "issues": ["Minor formatting issues"],
                "recommendations": ["Add more comments", "Improve error handling"]
            },
            "user_experience": {
                "score": 0.8,
                "issues": ["Navigation could be clearer"],
                "recommendations": ["Simplify user flow", "Add onboarding"]
            },
            "performance": {
                "score": 0.85,
                "issues": ["Some slow database queries"],
                "recommendations": ["Optimize queries", "Add caching"]
            },
            "security": {
                "score": 0.9,
                "issues": ["Minor security considerations"],
                "recommendations": ["Add input validation", "Implement rate limiting"]
            },
            "next_steps": [
                "Address high-priority issues",
                "Plan for next iteration",
                "Gather user feedback"
            ]
        } 