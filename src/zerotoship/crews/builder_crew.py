"""
Builder Crew for ZeroToShip.
Orchestrates code generation, development, and technical implementation.
"""

import asyncio
from typing import Dict, List, Optional, Any
from crewai import Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from pydantic import BaseModel, Field

from ..agents.builder_agent import BuilderAgent
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


@CrewBase
class BuilderCrew:
    """Builder Crew for comprehensive code generation and development."""
    
    def __init__(self, config: Optional[BuilderCrewConfig] = None):
        """Initialize the Builder Crew."""
        self.config = config or BuilderCrewConfig()
        self.memory_manager = ProjectMetaMemoryManager()
        self.builder_agent = BuilderAgent()
        
    @agent
    def code_architect(self) -> BuilderAgent:
        """Code architect agent for system design and architecture."""
        return self.builder_agent
    
    @agent
    def feature_implementer(self) -> BuilderAgent:
        """Feature implementer agent for coding specific features."""
        return BuilderAgent()
    
    @agent
    def test_engineer(self) -> BuilderAgent:
        """Test engineer agent for automated testing."""
        return BuilderAgent()
    
    @agent
    def documentation_specialist(self) -> BuilderAgent:
        """Documentation specialist agent for code documentation."""
        return BuilderAgent()
    
    @agent
    def code_reviewer(self) -> BuilderAgent:
        """Code reviewer agent for quality assurance."""
        return BuilderAgent()

    @task
    def system_architecture_design(self) -> Task:
        """Design system architecture and technical blueprint."""
        return Task(
            description="""
            Design comprehensive system architecture for the project.
            
            Focus on:
            1. Technology stack selection
            2. System architecture patterns
            3. Database design and data flow
            4. API design and integration points
            5. Scalability and performance considerations
            
            Provide detailed technical blueprint with architecture diagrams.
            """,
            agent=self.code_architect(),
            expected_output="Comprehensive system architecture with technical specifications."
        )

    @task
    def core_feature_implementation(self) -> Task:
        """Implement core features and functionality."""
        return Task(
            description="""
            Implement core features based on the system architecture.
            
            Implement:
            1. Core business logic and algorithms
            2. User interface components
            3. Data models and database schemas
            4. API endpoints and services
            5. Integration with external systems
            
            Provide working code with proper error handling and validation.
            """,
            agent=self.feature_implementer(),
            expected_output="Functional code implementation with core features.",
            context=["system_architecture_design"]
        )

    @task
    def automated_testing_suite(self) -> Task:
        """Create comprehensive automated testing suite."""
        return Task(
            description="""
            Develop comprehensive automated testing suite.
            
            Create:
            1. Unit tests for all components
            2. Integration tests for system interactions
            3. End-to-end tests for user workflows
            4. Performance and load tests
            5. Security and vulnerability tests
            
            Provide test coverage reports and automated test execution.
            """,
            agent=self.test_engineer(),
            expected_output="Comprehensive test suite with high coverage and automated execution.",
            context=["core_feature_implementation"]
        )

    @task
    def code_documentation_generation(self) -> Task:
        """Generate comprehensive code documentation."""
        return Task(
            description="""
            Generate comprehensive code documentation and guides.
            
            Create:
            1. API documentation and usage examples
            2. Code comments and inline documentation
            3. User guides and tutorials
            4. Developer setup and deployment guides
            5. Architecture and design documentation
            
            Provide clear, comprehensive documentation for all stakeholders.
            """,
            agent=self.documentation_specialist(),
            expected_output="Complete documentation suite with examples and guides.",
            context=["core_feature_implementation", "automated_testing_suite"]
        )

    @task
    def code_quality_review(self) -> Task:
        """Conduct comprehensive code quality review."""
        return Task(
            description="""
            Conduct comprehensive code quality review and optimization.
            
            Review:
            1. Code quality and best practices
            2. Performance optimization opportunities
            3. Security vulnerabilities and fixes
            4. Code maintainability and readability
            5. Technical debt identification and resolution
            
            Provide quality assessment with improvement recommendations.
            """,
            agent=self.code_reviewer(),
            expected_output="Code quality report with optimization recommendations.",
            context=["core_feature_implementation", "automated_testing_suite", "code_documentation_generation"]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Builder Crew."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )

    async def generate_code(self, execution_plan: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate code based on execution plan and requirements.
        
        Args:
            execution_plan: Detailed execution plan from ExecutionCrew
            context: Additional context for development
            
        Returns:
            Generated code and development artifacts
        """
        # Store execution plan in memory
        self.memory_manager.add_success_pattern(
            pattern={"execution_plan": execution_plan, "context": context},
            project_id="builder_crew",
            agent_id="builder_crew",
            confidence_score=0.8
        )
        
        # Execute the crew workflow
        inputs = {
            "execution_plan": execution_plan,
            "context": context or {},
            "development_steps": [
                "system_architecture_design",
                "core_feature_implementation",
                "automated_testing_suite",
                "code_documentation_generation",
                "code_quality_review"
            ]
        }
        
        result = await self.crew().kickoff(inputs=inputs)
        
        # Store development result in memory
        self.memory_manager.add_success_pattern(
            pattern={"development_result": result},
            project_id="builder_crew",
            agent_id="builder_crew",
            confidence_score=0.9
        )
        
        return {
            "code_files": result.get("code_files", []),
            "architecture": result.get("architecture", {}),
            "tests": result.get("tests", []),
            "documentation": result.get("documentation", {}),
            "deployment_config": result.get("deployment_config", {}),
            "quality_metrics": result.get("quality_metrics", {}),
            "build_artifacts": result.get("build_artifacts", [])
        }

    async def implement_feature(self, feature_spec: Dict[str, Any], codebase_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Implement specific feature based on specification.
        
        Args:
            feature_spec: Feature specification and requirements
            codebase_context: Current codebase context
            
        Returns:
            Implemented feature with tests and documentation
        """
        # Store feature implementation in memory
        self.memory_manager.add_success_pattern(
            pattern={"feature_implementation": {"spec": feature_spec, "context": codebase_context}},
            project_id="builder_crew",
            agent_id="builder_crew",
            confidence_score=0.8
        )
        
        # Execute feature implementation
        inputs = {
            "feature_spec": feature_spec,
            "codebase_context": codebase_context or {},
            "implementation_type": "feature_development"
        }
        
        result = await self.crew().kickoff(inputs=inputs)
        
        return {
            "feature_code": result.get("feature_code", ""),
            "unit_tests": result.get("unit_tests", []),
            "integration_tests": result.get("integration_tests", []),
            "documentation": result.get("documentation", ""),
            "api_changes": result.get("api_changes", []),
            "database_changes": result.get("database_changes", [])
        }

    async def run_tests(self, test_suite: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run comprehensive test suite and report results.
        
        Args:
            test_suite: Test suite configuration and tests
            
        Returns:
            Test results and quality metrics
        """
        # Store test execution in memory
        self.memory_manager.add_success_pattern(
            pattern={"test_execution": test_suite},
            project_id="builder_crew",
            agent_id="builder_crew",
            confidence_score=0.8
        )
        
        # Execute test suite
        inputs = {
            "test_suite": test_suite,
            "execution_type": "test_execution"
        }
        
        result = await self.crew().kickoff(inputs=inputs)
        
        return {
            "test_results": result.get("test_results", {}),
            "coverage_report": result.get("coverage_report", {}),
            "performance_metrics": result.get("performance_metrics", {}),
            "quality_score": result.get("quality_score", 0.0),
            "issues_found": result.get("issues_found", []),
            "recommendations": result.get("recommendations", [])
        }

    async def run_async(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the builder crew asynchronously.
        
        Args:
            project_data: Project data to process
            
        Returns:
            Build results and code artifacts
        """
        try:
            # Extract execution plan from project data
            execution_plan = project_data.get('execution_plan', {})
            
            # Generate code based on execution plan
            code_result = await self.generate_code(execution_plan, project_data)
            
            # Run tests on the generated code
            test_result = await self.run_tests({
                "code_files": code_result.get("code_files", []),
                "test_suite": code_result.get("tests", [])
            })
            
            # Combine results
            result = {
                "code_generation": code_result,
                "test_results": test_result,
                "status": "completed",
                "confidence": 0.85
            }
            
            return result
            
        except Exception as e:
            return {
                "error": str(e),
                "status": "failed",
                "confidence": 0.0
            } 