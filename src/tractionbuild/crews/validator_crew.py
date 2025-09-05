"""
Validator Crew for tractionbuild.
Orchestrates market research, competitor analysis, and idea validation.
"""

import asyncio
from typing import Dict, List, Optional, Any
from crewai import Crew, Agent, Task, Process
from pydantic import BaseModel, Field

from .base_crew import BaseCrew
from ..agents.validator_agent import ValidatorAgent
from ..tools.market_oracle_tool import MarketOracleTool
from ..core.project_meta_memory import ProjectMetaMemoryManager
from ..models.validation_result import ValidationResult
from ..tools.celery_execution_tool import CeleryExecutionTool
from ..utils.llm_factory import get_llm

class ValidatorCrewConfig(BaseModel):
    """Configuration for the Validator Crew."""
    enable_memory_learning: bool = Field(default=True, description="Enable memory learning")
    enable_market_research: bool = Field(default=True, description="Enable market research")
    enable_competitive_analysis: bool = Field(default=True, description="Enable competitive analysis")
    enable_market_sizing: bool = Field(default=True, description="Enable market sizing")
    enable_risk_assessment: bool = Field(default=True, description="Enable risk assessment")
    max_validation_iterations: int = Field(default=3, description="Maximum validation iterations")

class ValidatorCrew(BaseCrew):
    """Validates a business idea using real-time market data and compliance checks."""
    
    def __init__(self, project_data: Dict[str, Any], config: Optional[ValidatorCrewConfig] = None):
        self.config = config or ValidatorCrewConfig()
        self.memory_manager = ProjectMetaMemoryManager()
        self.validator_agent = ValidatorAgent()
        self.celery_executor = CeleryExecutionTool()
        super().__init__(project_data)

    def _create_crew(self) -> Crew:
        """Create the Validator Crew with agents and tasks."""
        context = self.get_project_context()
        idea = context.get("idea", "")

        # Get LLM from the factory
        llm = get_llm()

        # Create agents
        market_researcher = Agent(
            role="Market Research Specialist",
            goal="Conduct comprehensive market research and analysis",
            backstory="Expert with 15+ years in market analysis and trend identification",
            tools=[MarketOracleTool()],
            verbose=True,
            allow_delegation=False,
            llm=llm
        )

        competitor_analyst = Agent(
            role="Competitive Intelligence Analyst", 
            goal="Analyze competitive landscape and positioning opportunities",
            backstory="Specialist in competitive intelligence with deep industry knowledge",
            verbose=True,
            allow_delegation=False
        )

        market_sizer = Agent(
            role="Market Sizing Specialist",
            goal="Quantify market opportunities with TAM/SAM/SOM analysis", 
            backstory="Data-driven analyst expert in market sizing and financial modeling",
            verbose=True,
            allow_delegation=False
        )

        risk_assessor = Agent(
            role="Risk Assessment Specialist",
            goal="Identify and evaluate market and business risks",
            backstory="Risk management expert with experience across multiple industries",
            verbose=True,
            allow_delegation=False
        )

        validation_synthesizer = Agent(
            role="Validation Synthesis Specialist",
            goal="Synthesize validation findings into actionable recommendations",
            backstory="Strategic advisor with expertise in business validation and go-to-market strategy",
            verbose=True,
            allow_delegation=False
        )

        # Create tasks
        market_research_task = Task(
            description=f"""
            Analyze the provided idea through comprehensive market research.
            Focus on: 1. Market size, 2. Target audience,
            3. Market trends, 4. Opportunity assessment.
            Use real-time data and market insights.
            Idea: {idea}
            Provide detailed findings.
            """,
            agent=market_researcher,
            expected_output="Comprehensive market research report with insights."
        )

        competitor_analysis_task = Task(
            description=f"""
            Conduct thorough competitor analysis for the idea.
            Analyze: 1. Direct/indirect competitors, 2. Advantages/disadvantages,
            3. Positioning opportunities, 4. Competitive gaps.
            Idea: {idea}
            Provide strategic insights.
            """,
            agent=competitor_analyst,
            expected_output="Strategic competitive analysis with recommendations.",
            context=[market_research_task]
        )

        market_sizing_task = Task(
            description=f"""
            Quantify the market size and opportunity potential.
            Calculate: 1. TAM, 2. SAM, 3. SOM, 4. Growth rates.
            Idea: {idea}
            Provide market size estimates.
            """,
            agent=market_sizer,
            expected_output="Quantified market size analysis with TAM/SAM/SOM breakdown.",
            context=[market_research_task, competitor_analysis_task]
        )

        risk_assessment_task = Task(
            description=f"""
            Conduct comprehensive risk assessment for the idea.
            Evaluate: 1. Market risks, 2. Competitive threats,
            3. Technical challenges, 4. Regulatory, 5. Resource risks.
            Idea: {idea}
            Provide mitigation strategies.
            """,
            agent=risk_assessor,
            expected_output="Comprehensive risk assessment with mitigation strategies.",
            context=[market_sizing_task, competitor_analysis_task]
        )

        synthesis_task = Task(
            description=f"""
            Synthesize all validation findings into a recommendation.
            Integrate: 1. Market insights, 2. Competitive analysis,
            3. Market sizing, 4. Risk assessment, 5. Opportunity evaluation.
            Idea: {idea}
            Provide go/no-go recommendation.
            """,
            agent=validation_synthesizer,
            expected_output="Final validation recommendation with confidence score.",
            context=[market_research_task, competitor_analysis_task, market_sizing_task, risk_assessment_task]
        )

        return Crew(
            agents=[market_researcher, competitor_analyst, market_sizer, risk_assessor, validation_synthesizer],
            tasks=[market_research_task, competitor_analysis_task, market_sizing_task, risk_assessment_task, synthesis_task],
            process=Process.sequential,
            verbose=True,
        )

    async def _execute_crew(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the Validator Crew using distributed execution."""
        try:
            # Execute the crew directly using CrewAI
            result = await self.crew.kickoff_async(inputs=inputs)
            return {"validation_result": result, "status": "success"}
        except Exception as e:
            logger.error(f"ValidatorCrew execution failed: {e}")
            return {"error": str(e), "status": "failed"}

    async def validate_idea(self, idea: str, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        Validate a business idea using comprehensive market research.
        
        Args:
            idea: The business idea to validate
            context: Additional context for validation
            
        Returns:
            ValidationResult with comprehensive analysis
        """
        # Store validation request in memory
        self.memory_manager.add_success_pattern(
            pattern={"validation_request": {"idea": idea, "context": context}},
            project_id="validator_crew",
            agent_id="validator_crew", 
            confidence_score=0.8
        )
        
        # Execute the crew workflow
        project_data = self.project_data.copy()
        project_data.update({"idea": idea, "context": context or {}})
        
        result = await self._execute_crew(project_data)
        
        # Store validation result in memory
        self.memory_manager.add_success_pattern(
            pattern={"validation_result": result},
            project_id="validator_crew",
            agent_id="validator_crew",
            confidence_score=0.9
        )
        
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
        Analyze market data and trends.
        
        Args:
            market_data: Market data to analyze
            
        Returns:
            Market analysis results
        """
        # Store market analysis in memory
        self.memory_manager.add_success_pattern(
            pattern={"market_analysis": market_data},
            project_id="validator_crew",
            agent_id="validator_crew",
            confidence_score=0.8
        )
        
        # Execute market analysis
        project_data = self.project_data.copy()
        project_data.update({"market_data": market_data, "analysis_type": "market_analysis"})
        
        result = await self._execute_crew(project_data)
        
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
        Scope MVP requirements for the idea.
        
        Args:
            idea: The business idea to scope
            constraints: Resource and timeline constraints
            
        Returns:
            MVP scope and requirements
        """
        # Store MVP scoping in memory
        self.memory_manager.add_success_pattern(
            pattern={"mvp_scoping": {"idea": idea, "constraints": constraints}},
            project_id="validator_crew",
            agent_id="validator_crew",
            confidence_score=0.8
        )
        
        # Execute MVP scoping
        project_data = self.project_data.copy()
        project_data.update({
            "idea": idea, 
            "constraints": constraints or {},
            "analysis_type": "mvp_scoping"
        })
        
        result = await self._execute_crew(project_data)
        
        return {
            "core_features": result.get("core_features", []),
            "timeline": result.get("timeline", "TBD"),
            "budget": result.get("budget", "TBD"),
            "team_size": result.get("team_size", "TBD"),
            "success_metrics": result.get("success_metrics", [])
        }