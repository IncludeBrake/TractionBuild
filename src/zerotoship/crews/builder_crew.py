"""
Builder Crew for ZeroToShip.
Orchestrates code generation, development, and technical implementation.
"""

import asyncio
from typing import Dict, List, Optional, Any
from crewai import Crew, Agent, Task, Process
from pydantic import BaseModel, Field

from .base_crew import BaseCrew
from ..tools.code_tools import CodeTools
from ..tools.mermaid_tools import MermaidTools
from ..core.project_meta_memory import ProjectMetaMemoryManager

class BuilderCrewConfig(BaseModel):
    """Configuration for the Builder Crew."""
    enable_memory_learning: bool = Field(default=True, description="Enable memory learning")
    enable_code_generation: bool = Field(default=True, description="Enable code generation")
    max_build_iterations: int = Field(default=3, description="Maximum build iterations")
    enable_testing: bool = Field(default=True, description="Enable automated testing")
    enable_documentation: bool = Field(default=True, description="Enable code documentation")

class BuilderCrew(BaseCrew):
    """
    The BuilderCrew is a specialized team of AI agents that handles the entire
    software development lifecycle, from system architecture to code generation,
    testing, and documentation.
    """

    def __init__(self, project_data: Dict[str, Any], config: Optional[BuilderCrewConfig] = None):
        """Initialize the Builder Crew with project data and config."""
        super().__init__(project_data)
        self.config = config or BuilderCrewConfig()
        self.memory_manager = ProjectMetaMemoryManager()

    def _create_crew(self) -> Crew:
        """
        Defines the agents and tasks that form the BuilderCrew.
        This method is called by the BaseCrew's __init__.
        """
        
        # 1. --- DEFINE SPECIALIZED AGENTS ---
        
        code_architect = Agent(
            role="Principal Software Architect",
            goal="Design a robust, scalable, and maintainable software architecture based on the project requirements.",
            backstory="You are a seasoned software architect with 20 years of experience designing enterprise-grade systems. You think in terms of design patterns, scalability, and long-term maintainability.",
            tools=[MermaidTools()], # e.g., MermaidTools for diagrams
            allow_delegation=False,
            verbose=True
        )

        feature_implementer = Agent(
            role="Senior Full-Stack Developer",
            goal="Write high-quality, production-ready code to implement the specified features.",
            backstory="You are a pragmatic and efficient developer who excels at turning architectural plans into clean, functional code. You follow best practices and write code that is easy for others to understand.",
            tools=[CodeTools()], # e.g., CodeTools, FileTools
            allow_delegation=False,
            verbose=True
        )

        test_engineer = Agent(
            role="QA and Test Automation Engineer",
            goal="Ensure the code is bug-free and meets all quality standards by creating a comprehensive suite of automated tests.",
            backstory="You have a keen eye for detail and a passion for quality. You are an expert in creating robust unit, integration, and end-to-end tests that catch issues before they reach production.",
            tools=[CodeTools()], # e.g., CodeTools for test generation
            allow_delegation=False,
            verbose=True
        )

        documentation_specialist = Agent(
            role="Technical Writer",
            goal="Create clear, comprehensive, and user-friendly documentation for the codebase.",
            backstory="You are a skilled writer who can make complex technical concepts easy to understand. You create documentation that empowers both developers and end-users.",
            tools=[],
            allow_delegation=False,
            verbose=True
        )

        # 2. --- DEFINE THE SEQUENTIAL TASKS ---

        task_architecture = Task(
            description="Based on the project idea and requirements provided in the inputs, design a comprehensive system architecture. "
                        "Define the technology stack, data models, API endpoints, and overall structure.",
            expected_output="A detailed technical blueprint document, including a Mermaid diagram of the architecture.",
            agent=code_architect
        )

        task_implementation = Task(
            description="Using the system architecture blueprint, write the source code for the core features. "
                        "Ensure the code is clean, well-commented, and adheres to best practices.",
            expected_output="A set of source code files that implement the core functionality.",
            agent=feature_implementer,
            context=[task_architecture] # This task depends on the output of the architecture task
        )
        
        task_testing = Task(
            description="Create and run a comprehensive suite of automated tests (unit, integration) for the generated code. "
                        "Ensure at least 80% test coverage.",
            expected_output="A complete set of test files and a test coverage report.",
            agent=test_engineer,
            context=[task_implementation]
        )

        task_documentation = Task(
            description="Generate comprehensive documentation for the code, including API docs and a README file with setup instructions.",
            expected_output="A complete set of documentation files in Markdown format.",
            agent=documentation_specialist,
            context=[task_implementation, task_testing]
        )
        
        # 3. --- ASSEMBLE AND RETURN THE CREW ---
        
        return Crew(
            agents=[code_architect, feature_implementer, test_engineer, documentation_specialist],
            tasks=[task_architecture, task_implementation, task_testing, task_documentation],
            process=Process.sequential,
            verbose=True
        )

    async def generate_code(self, execution_plan: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate code based on execution plan and context."""
        project_data = self.project_data.copy()
        project_data.update({"execution_plan": execution_plan, "context": context})
        result = await self.run_async(project_data)
        return result.get("builder", {})

    async def implement_feature(self, feature_spec: Dict[str, Any], codebase_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Implement a specific feature based on specification."""
        project_data = self.project_data.copy()
        project_data.update({"feature_spec": feature_spec, "codebase_context": codebase_context})
        result = await self.run_async(project_data)
        return result.get("builder", {})

    async def run_tests(self, test_suite: Dict[str, Any]) -> Dict[str, Any]:
        """Run tests on the codebase."""
        project_data = self.project_data.copy()
        project_data.update({"test_suite": test_suite})
        result = await self.run_async(project_data)
        return result.get("builder", {})
