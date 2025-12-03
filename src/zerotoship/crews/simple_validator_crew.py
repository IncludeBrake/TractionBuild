"""
Simple Validator Crew - Real AI Implementation
Uses CrewAI to validate product viability and readiness.
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


class SimpleValidatorCrew(CrewAIAdapter):
    """
    Validator crew that validates technical and market readiness.
    Focuses on:
    - Technical validation
    - Market validation
    - Risk assessment
    - Launch readiness
    """

    def __init__(self, project_data: Dict[str, Any]):
        """Initialize the Validator Crew."""
        if not CREWAI_AVAILABLE:
            raise ImportError("CrewAI not available")

        super().__init__(project_data)
        self.idea = project_data.get("idea", "Unknown product")

    def create_agents(self) -> List[Agent]:
        """Create the validator agents."""

        # QA Specialist Agent
        qa_specialist = Agent(
            role="QA Specialist",
            goal=f"Validate technical readiness and quality for: {self.idea}",
            backstory=(
                "You are a meticulous QA specialist with expertise in testing strategies, "
                "quality assurance, and launch readiness. You know how to identify potential "
                "issues before they become problems and ensure products meet quality standards."
            ),
            verbose=True,
            allow_delegation=False
        )

        # Product Validator Agent
        product_validator = Agent(
            role="Product Validator",
            goal=f"Validate market fit and product readiness for: {self.idea}",
            backstory=(
                "You are an experienced product validator who specializes in assessing "
                "product-market fit. You understand user needs, competitive positioning, "
                "and what it takes to succeed in the market."
            ),
            verbose=True,
            allow_delegation=False
        )

        return [qa_specialist, product_validator]

    def create_tasks(self, agents: List[Agent]) -> List[Task]:
        """Create the validation tasks."""

        qa_specialist, product_validator = agents

        # Task 1: Technical Validation
        technical_validation_task = Task(
            description=f"""
            Perform technical validation for: {self.idea}

            Validate:
            1. Architecture soundness and scalability
            2. Security vulnerabilities and risks
            3. Performance bottlenecks
            4. Testing coverage requirements
            5. Deployment readiness
            6. Technical debt assessment

            Provide a go/no-go recommendation with specific action items if issues are found.
            """,
            agent=qa_specialist,
            expected_output="Technical validation report with go/no-go recommendation and action items"
        )

        # Task 2: Product/Market Validation
        product_validation_task = Task(
            description=f"""
            Perform product-market validation for: {self.idea}

            Validate:
            1. Product-market fit assessment
            2. Value proposition clarity
            3. Competitive differentiation
            4. Target audience alignment
            5. Launch readiness checklist
            6. Success criteria definition

            Provide a comprehensive validation report with recommendations.
            """,
            agent=product_validator,
            expected_output="Product-market validation report with launch readiness assessment"
        )

        return [technical_validation_task, product_validation_task]

    def get_next_state(self) -> str:
        """Validation leads to launch."""
        return "LAUNCH"
