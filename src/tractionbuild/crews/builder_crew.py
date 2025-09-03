"""
Builder Crew for tractionbuild.
Orchestrates code generation, development, and technical implementation.
"""

import asyncio
from typing import Dict, List, Optional, Any
from crewai import Crew, Process, Task
from pydantic import BaseModel, Field

from ..agents.builder_agent import BuilderAgent
from ..tools.code_tools import CodeTools
from ..tools.mermaid_tools import MermaidTools
from ..tools.compliance_tool import ComplianceCheckerTool
from ..tools.celery_execution_tool import CeleryExecutionTool
from ..core.project_meta_memory import ProjectMetaMemoryManager
from .base_crew import BaseCrew
from ..utils.llm_factory import get_llm

class BuilderCrewConfig(BaseModel):
    """Configuration for the Builder Crew."""
    enable_memory_learning: bool = Field(default=True, description="Enable memory learning")
    enable_code_generation: bool = Field(default=True, description="Enable code generation")
    max_build_iterations: int = Field(default=3, description="Maximum build iterations")
    enable_testing: bool = Field(default=True, description="Enable automated testing")
    enable_documentation: bool = Field(default=True, description="Enable code documentation")

class BuilderCrew(BaseCrew):
    """Builder Crew for comprehensive code generation and development."""
    
    def __init__(self, project_data: Dict[str, Any], config: Optional[BuilderCrewConfig] = None):
        super().__init__(project_data)
        self.config = config or BuilderCrewConfig()
        self.memory_manager = ProjectMetaMemoryManager()
        self.builder_agent = BuilderAgent()
        self.celery_executor = CeleryExecutionTool()

    def _create_crew(self) -> Crew:
        """Create the Builder Crew with agents and tasks."""
        # Get LLM from the factory
        llm = get_llm()
        
        agents = [
            BuilderAgent(tools=[ComplianceCheckerTool()], llm=llm).agent,
            BuilderAgent(llm=llm).agent,
            BuilderAgent(llm=llm).agent,
            BuilderAgent(llm=llm).agent,
            BuilderAgent(tools=[ComplianceCheckerTool()], llm=llm).agent,
        ]

        # Create tasks separately to avoid forward references
        task1 = Task(
            description="""
            Design comprehensive system architecture for the project.
            Focus on: 1. Technology stack selection, 2. System architecture patterns,
            3. Database design, 4. API design, 5. Scalability considerations.
            Ensure GDPR compliance during design.
            Provide blueprint with diagrams.
            """,
            agent=agents[0],
            expected_output="Comprehensive system architecture with technical specs."
        )
        
        task2 = Task(
            description="""
            Implement core features based on architecture.
            Implement: 1. Business logic, 2. UI components, 3. Data models,
            4. API endpoints, 5. External integrations.
            Provide code with error handling.
            """,
            agent=agents[1],
            expected_output="Functional code implementation.",
            context=[task1]
        )
        
        task3 = Task(
            description="""
            Develop automated testing suite.
            Create: 1. Unit tests, 2. Integration tests, 3. E2E tests,
            4. Performance tests, 5. Security tests.
            Provide coverage reports.
            """,
            agent=agents[2],
            expected_output="Comprehensive test suite with high coverage.",
            context=[task2]
        )
        
        task4 = Task(
            description="""
            Generate code documentation.
            Create: 1. API docs, 2. Code comments, 3. User guides,
            4. Developer guides, 5. Architecture docs.
            Provide clear documentation.
            """,
            agent=agents[3],
            expected_output="Complete documentation suite.",
            context=[task2, task3]
        )
        
        task5 = Task(
            description="""
            Conduct code quality review.
            Review: 1. Code quality, 2. Performance, 3. Security,
            4. Maintainability, 5. Technical debt.
            Ensure GDPR compliance.
            Provide quality assessment.
            """,
            agent=agents[4],
            expected_output="Code quality report with recommendations.",
            context=[task2, task3, task4]
        )
        
        tasks = [task1, task2, task3, task4, task5]

        return Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
        )

    async def _execute_crew(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the Builder Crew using distributed execution."""
        task_type = next(iter(inputs.keys()), "generate_code")  # Default to generate_code
        task_result = await self.celery_executor.execute_task(
            lambda: self.crew.kickoff_async(inputs=inputs)
        )
        result = task_result.result() if task_result else {}
        return result.get(task_type, {})

    async def generate_code(self, execution_plan: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        project_data = self.project_data.copy()
        project_data.update({"execution_plan": execution_plan, "context": context})
        return await self._execute_crew(project_data)

    async def implement_feature(self, feature_spec: Dict[str, Any], codebase_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        project_data = self.project_data.copy()
        project_data.update({"feature_spec": feature_spec, "codebase_context": codebase_context})
        return await self._execute_crew(project_data)

    async def run_tests(self, test_suite: Dict[str, Any]) -> Dict[str, Any]:
        project_data = self.project_data.copy()
        project_data.update({"test_suite": test_suite})
        return await self._execute_crew(project_data)