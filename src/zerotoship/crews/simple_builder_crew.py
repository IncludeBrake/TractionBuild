"""
Simple Builder Crew - Real AI Implementation
Uses CrewAI to plan and design technical implementations.
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


class SimpleBuilderCrew(CrewAIAdapter):
    """
    Builder crew that creates technical architecture and implementation plans.
    Focuses on:
    - System architecture design
    - Technology stack selection
    - Feature breakdown
    - Development roadmap
    """

    def __init__(self, project_data: Dict[str, Any]):
        """Initialize the Builder Crew."""
        if not CREWAI_AVAILABLE:
            raise ImportError("CrewAI not available")

        super().__init__(project_data)
        self.idea = project_data.get("idea", "Unknown product")

    def create_agents(self) -> List[Agent]:
        """Create the builder agents."""

        # Solutions Architect Agent
        solutions_architect = Agent(
            role="Solutions Architect",
            goal=f"Design a scalable and maintainable architecture for: {self.idea}",
            backstory=(
                "You are a seasoned solutions architect with expertise in designing "
                "modern software systems. You excel at choosing the right technologies, "
                "designing clean architectures, and ensuring systems are scalable, "
                "maintainable, and secure."
            ),
            verbose=True,
            allow_delegation=False
        )

        # Tech Lead Agent
        tech_lead = Agent(
            role="Technical Lead",
            goal=f"Break down features and create a development roadmap for: {self.idea}",
            backstory=(
                "You are an experienced technical lead who excels at breaking down "
                "complex projects into manageable tasks. You understand agile development, "
                "prioritization, and how to create realistic timelines. You know how to "
                "identify MVP features and plan iterative releases."
            ),
            verbose=True,
            allow_delegation=False
        )

        # DevOps Engineer Agent
        devops_engineer = Agent(
            role="DevOps Engineer",
            goal=f"Define deployment strategy and infrastructure for: {self.idea}",
            backstory=(
                "You are a skilled DevOps engineer who specializes in setting up CI/CD "
                "pipelines, cloud infrastructure, and monitoring solutions. You know how "
                "to balance cost, performance, and reliability in deployment strategies."
            ),
            verbose=True,
            allow_delegation=False
        )

        return [solutions_architect, tech_lead, devops_engineer]

    def create_tasks(self, agents: List[Agent]) -> List[Task]:
        """Create the builder tasks."""

        solutions_architect, tech_lead, devops_engineer = agents

        # Task 1: System Architecture
        architecture_task = Task(
            description=f"""
            Design a comprehensive system architecture for: {self.idea}

            Your architecture should include:
            1. High-level system components and their relationships
            2. Technology stack recommendations (frontend, backend, database, etc.)
            3. Data models and database schema design
            4. API design and endpoints
            5. Security considerations and authentication strategy
            6. Scalability and performance considerations

            Focus on creating an MVP-ready architecture that can evolve over time.
            Be specific about technology choices and justify your decisions.
            """,
            agent=solutions_architect,
            expected_output="A detailed system architecture document with technology stack, data models, and API design"
        )

        # Task 2: Feature Breakdown and Roadmap
        roadmap_task = Task(
            description=f"""
            Create a development roadmap and feature breakdown for: {self.idea}

            Your roadmap should include:
            1. MVP feature list (core features only)
            2. Phase 1 feature list (post-MVP enhancements)
            3. Phase 2 feature list (future enhancements)
            4. User stories for MVP features (in agile format)
            5. Estimated complexity for each feature (simple/medium/complex)
            6. Development timeline (sprint-by-sprint breakdown)
            7. Dependencies and critical path

            Ensure the MVP is achievable and provides real value to users.
            """,
            agent=tech_lead,
            expected_output="A complete development roadmap with MVP features, user stories, and timeline"
        )

        # Task 3: Deployment Strategy
        deployment_task = Task(
            description=f"""
            Define deployment strategy and infrastructure for: {self.idea}

            Your strategy should include:
            1. Cloud platform recommendation (AWS/GCP/Azure/other)
            2. Infrastructure components (servers, databases, storage, etc.)
            3. CI/CD pipeline design (build, test, deploy)
            4. Monitoring and logging strategy
            5. Backup and disaster recovery plan
            6. Estimated monthly infrastructure costs (for MVP scale)
            7. Scaling strategy as user base grows

            Optimize for startup-friendly costs while maintaining reliability.
            """,
            agent=devops_engineer,
            expected_output="A comprehensive deployment strategy with infrastructure design, CI/CD pipeline, and cost estimates"
        )

        return [architecture_task, roadmap_task, deployment_task]

    def get_next_state(self) -> str:
        """Builder leads to marketing preparation."""
        return "MARKETING_PREPARATION"
