"""
Validator Crew for ZeroToShip.
Orchestrates market research, competitor analysis, and idea validation.
"""

import asyncio
from typing import Dict, List, Optional, Any
from crewai import Crew, Process, Task, Agent
from pydantic import BaseModel, Field

from .base_crew import BaseCrew
from ..agents.validator_agent import ValidatorAgent
from ..tools.market_tools import MarketTools
from ..models.market_data import ValidationResult
from ..core.project_meta_memory import ProjectMetaMemoryManager


class ValidatorCrewConfig(BaseModel):
    """Configuration for the Validator Crew."""
    
    enable_memory_learning: bool = Field(default=True, description="Enable memory learning")
    enable_sequential_validation: bool = Field(default=True, description="Enable sequential validation steps")
    max_validation_iterations: int = Field(default=3, description="Maximum validation iterations")
    enable_competitor_analysis: bool = Field(default=True, description="Enable competitor analysis")
    enable_market_sizing: bool = Field(default=True, description="Enable market sizing")


class ValidatorCrew(BaseCrew):
    """Validator Crew for comprehensive idea validation and market research."""
    
    def __init__(self, project_data: Dict[str, Any]):
        """Initialize the Validator Crew with project data."""
        self.memory_manager = ProjectMetaMemoryManager()
        self.validator_agent = ValidatorAgent()
        
        # Create CrewAI agents before calling super().__init__
        self.market_researcher = Agent(
            role="Market Research Specialist",
            goal="Conduct comprehensive market research and analysis",
            backstory="Expert market researcher with 15+ years of experience in startup validation and market analysis",
            verbose=True,
            allow_delegation=False
        )
        
        self.competitor_analyst = Agent(
            role="Competitive Intelligence Analyst",
            goal="Analyze competitive landscape and identify market opportunities",
            backstory="Strategic analyst specializing in competitive intelligence and market positioning",
            verbose=True,
            allow_delegation=False
        )
        
        self.market_sizer = Agent(
            role="Market Sizing Specialist",
            goal="Quantify market size and opportunity potential",
            backstory="Data-driven analyst with expertise in market sizing and opportunity quantification",
            verbose=True,
            allow_delegation=False
        )
        
        self.risk_assessor = Agent(
            role="Risk Assessment Specialist",
            goal="Identify and assess market risks and challenges",
            backstory="Risk management expert with deep understanding of startup and market risks",
            verbose=True,
            allow_delegation=False
        )
        
        self.validation_synthesizer = Agent(
            role="Validation Synthesis Specialist",
            goal="Synthesize all findings into comprehensive validation recommendations",
            backstory="Strategic advisor with expertise in startup validation and go/no-go decisions",
            verbose=True,
            allow_delegation=False
        )
        
        # Call super().__init__ after agents are created
        super().__init__(project_data)

    def _create_crew(self) -> Crew:
        """Create the CrewAI crew for validation tasks."""
        # Get project context
        context = self.get_project_context()
        idea = context.get("idea", "")
        
        # Create tasks
        tasks = []
        
        # Task 1: Initial Market Research
        tasks.append(Task(
            description=f"""
            Analyze the provided idea through comprehensive market research.
            
            Focus on:
            1. Market size and growth potential
            2. Target audience identification
            3. Current market trends
            4. Initial opportunity assessment
            
            Idea: {idea}
            
            Provide detailed findings with data-driven insights.
            """,
            agent=self.market_researcher,
            expected_output="Comprehensive market research report with key insights and data points."
        ))
        
        # Task 2: Competitor Analysis
        tasks.append(Task(
            description=f"""
            Conduct thorough competitor analysis for the idea.
            
            Analyze:
            1. Direct and indirect competitors
            2. Competitive advantages and disadvantages
            3. Market positioning opportunities
            4. Competitive gaps and white space
            
            Idea: {idea}
            
            Provide strategic competitive insights.
            """,
            agent=self.competitor_analyst,
            expected_output="Strategic competitive analysis with positioning recommendations."
        ))
        
        # Task 3: Market Sizing
        tasks.append(Task(
            description=f"""
            Quantify the market size and opportunity potential.
            
            Calculate:
            1. Total Addressable Market (TAM)
            2. Serviceable Addressable Market (SAM)
            3. Serviceable Obtainable Market (SOM)
            4. Market growth rates and trends
            
            Idea: {idea}
            
            Provide concrete market size estimates with methodology.
            """,
            agent=self.market_sizer,
            expected_output="Quantified market size analysis with TAM/SAM/SOM breakdown."
        ))
        
        # Task 4: Risk Assessment
        tasks.append(Task(
            description=f"""
            Conduct comprehensive risk assessment for the idea.
            
            Evaluate:
            1. Market risks and uncertainties
            2. Competitive threats
            3. Technical challenges
            4. Regulatory considerations
            5. Resource and execution risks
            
            Idea: {idea}
            
            Provide risk mitigation strategies.
            """,
            agent=self.risk_assessor,
            expected_output="Comprehensive risk assessment with mitigation strategies."
        ))
        
        # Task 5: Validation Synthesis
        tasks.append(Task(
            description=f"""
            Synthesize all validation findings into a comprehensive recommendation.
            
            Integrate:
            1. Market research insights
            2. Competitive analysis
            3. Market sizing data
            4. Risk assessment
            5. Opportunity evaluation
            
            Idea: {idea}
            
            Provide clear go/no-go recommendation with confidence level.
            """,
            agent=self.validation_synthesizer,
            expected_output="Final validation recommendation with confidence score."
        ))
        
        # Create and return the crew
        return Crew(
            agents=[
                self.market_researcher,
                self.competitor_analyst,
                self.market_sizer,
                self.risk_assessor,
                self.validation_synthesizer
            ],
            tasks=tasks,
            process=Process.sequential,
            verbose=True
        )

    def _create_validation_tasks(self) -> List[Task]:
        """Create validation tasks for the crew."""
        tasks = []
        
        # Task 1: Initial Market Research
        tasks.append(Task(
            description="""
            Analyze the provided idea through comprehensive market research.
            
            Focus on:
            1. Market size and growth potential
            2. Target audience identification
            3. Current market trends
            4. Initial opportunity assessment
            
            Provide detailed findings with data-driven insights.
            """,
            agent=self.market_researcher,
            expected_output="Comprehensive market research report with key insights and data points."
        ))
        
        # Task 2: Competitor Analysis
        tasks.append(Task(
            description="""
            Conduct thorough competitor analysis for the idea.
            
            Analyze:
            1. Direct and indirect competitors
            2. Competitive advantages and disadvantages
            3. Market positioning opportunities
            4. Competitive gaps and white space
            
            Provide strategic competitive insights.
            """,
            agent=self.competitor_analyst,
            expected_output="Detailed competitor analysis with strategic positioning recommendations.",
            context=[tasks[0]] if tasks else None
        ))
        
        # Task 3: Market Sizing
        tasks.append(Task(
            description="""
            Quantify the market size and opportunity potential.
            
            Calculate:
            1. Total Addressable Market (TAM)
            2. Serviceable Addressable Market (SAM)
            3. Serviceable Obtainable Market (SOM)
            4. Market growth rates and trends
            
            Provide concrete market size estimates with methodology.
            """,
            agent=self.market_sizer,
            expected_output="Quantified market size analysis with TAM/SAM/SOM breakdown.",
            context=[tasks[0], tasks[1]] if len(tasks) >= 2 else None
        ))
        
        # Task 4: Risk Assessment
        tasks.append(Task(
            description="""
            Conduct comprehensive risk assessment for the idea.
            
            Evaluate:
            1. Market risks and uncertainties
            2. Competitive threats
            3. Technical challenges
            4. Regulatory considerations
            5. Resource and execution risks
            
            Provide risk mitigation strategies.
            """,
            agent=self.risk_assessor,
            expected_output="Comprehensive risk assessment with mitigation strategies.",
            context=[tasks[2], tasks[1]] if len(tasks) >= 3 else None
        ))
        
        # Task 5: Final Synthesis
        tasks.append(Task(
            description="""
            Synthesize all validation findings into a comprehensive recommendation.
            
            Integrate:
            1. Market research insights
            2. Competitive analysis
            3. Market sizing data
            4. Risk assessment
            5. Opportunity evaluation
            
            Provide clear go/no-go recommendation with confidence level.
            """,
            agent=self.validation_synthesizer,
            expected_output="Final validation result with recommendation and confidence score.",
            context=tasks[:-1] if len(tasks) >= 4 else None
        ))
        
        return tasks

    def create_crew(self) -> Crew:
        """Create the Validator Crew."""
        tasks = self._create_validation_tasks()
        
        return Crew(
            agents=[
                self.market_researcher,
                self.competitor_analyst,
                self.market_sizer,
                self.risk_assessor,
                self.validation_synthesizer
            ],
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
        )

    async def validate_idea(self, idea: str, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        Validate an idea through comprehensive market research and analysis.
        
        Args:
            idea: The idea to validate
            context: Additional context for validation
            
        Returns:
            ValidationResult with comprehensive analysis and recommendations
        """
        # Store initial idea in memory
        self.memory_manager.add_success_pattern(
            pattern={"idea": idea, "context": context},
            project_id="validator_crew",
            agent_id="validator_crew",
            confidence_score=0.8
        )
        
        # Create and execute the crew
        crew = self.create_crew()
        
        # Execute the crew workflow
        inputs = {
            "idea": idea,
            "context": context or {},
            "validation_steps": [
                "initial_market_research",
                "competitor_landscape_analysis", 
                "market_sizing_quantification",
                "comprehensive_risk_assessment",
                "final_validation_synthesis"
            ]
        }
        
        result = await crew.kickoff(inputs=inputs)
        
        # Store validation result in memory
        self.memory_manager.add_success_pattern(
            pattern={"validation_result": result},
            project_id="validator_crew",
            agent_id="validator_crew",
            confidence_score=0.9
        )
        
        # Convert result to ValidationResult format
        return ValidationResult(
            idea=idea,
            market_size=result.get("market_size", "TBD"),
            competition_level=result.get("competition_level", "medium"),
            target_audience=result.get("target_audience", "TBD"),
            mvp_scope=result.get("mvp_scope", "TBD"),
            risks=result.get("risks", "TBD"),
            recommendation=result.get("recommendation", "go"),
            confidence_score=result.get("confidence_score", 0.7),
            reasoning=result.get("reasoning", "Comprehensive validation completed"),
            estimated_timeline=result.get("estimated_timeline", "TBD"),
            estimated_budget=result.get("estimated_budget", "TBD")
        )

    async def analyze_market(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze market data and provide insights.
        
        Args:
            market_data: Market data to analyze
            
        Returns:
            Analysis results
        """
        # Store market analysis in memory
        self.memory_manager.add_success_pattern(
            pattern={"market_analysis": market_data},
            project_id="validator_crew",
            agent_id="validator_crew",
            confidence_score=0.8
        )
        
        # Create a focused crew for market analysis
        crew = Crew(
            agents=[self.market_researcher, self.market_sizer],
            tasks=[
                Task(
                    description="Analyze the provided market data and provide comprehensive insights.",
                    agent=self.market_researcher,
                    expected_output="Market analysis report with key insights."
                ),
                Task(
                    description="Quantify market opportunities based on the analysis.",
                    agent=self.market_sizer,
                    expected_output="Market sizing and opportunity quantification.",
                    context=[0]  # Reference to previous task
                )
            ],
            process=Process.sequential,
            verbose=True
        )
        
        result = await crew.kickoff(inputs={"market_data": market_data})
        
        return {
            "market_size": result.get("market_size", "TBD"),
            "growth_rate": result.get("growth_rate", "TBD"),
            "key_players": result.get("key_players", []),
            "trends": result.get("trends", []),
            "opportunities": result.get("opportunities", []),
            "threats": result.get("threats", [])
        }

    async def scope_mvp(self, idea: str, constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Define MVP scope based on idea and constraints.
        
        Args:
            idea: The idea to scope
            constraints: Budget, timeline, or technical constraints
            
        Returns:
            MVP scope definition
        """
        # Store MVP scoping in memory
        self.memory_manager.add_success_pattern(
            pattern={"mvp_scoping": {"idea": idea, "constraints": constraints}},
            project_id="validator_crew",
            agent_id="validator_crew",
            confidence_score=0.8
        )
        
        # Create a focused crew for MVP scoping
        crew = Crew(
            agents=[self.market_researcher, self.validation_synthesizer],
            tasks=[
                Task(
                    description="Analyze the idea and define core MVP requirements.",
                    agent=self.market_researcher,
                    expected_output="MVP requirements analysis."
                ),
                Task(
                    description="Define MVP scope based on requirements and constraints.",
                    agent=self.validation_synthesizer,
                    expected_output="Comprehensive MVP scope definition.",
                    context=[0]  # Reference to previous task
                )
            ],
            process=Process.sequential,
            verbose=True
        )
        
        result = await crew.kickoff(inputs={"idea": idea, "constraints": constraints or {}})
        
        return {
            "core_features": result.get("core_features", []),
            "timeline": result.get("timeline", "TBD"),
            "budget": result.get("budget", "TBD"),
            "team_size": result.get("team_size", "TBD"),
            "success_metrics": result.get("success_metrics", [])
        }

 