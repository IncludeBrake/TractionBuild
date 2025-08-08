"""
Launch Crew for ZeroToShip.
Orchestrates launch preparation, execution, and post-launch activities.
"""

import asyncio
from typing import Dict, List, Optional, Any
from crewai import Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from pydantic import BaseModel, Field

from ..agents.launch_agent import LaunchAgent
from ..core.project_meta_memory import ProjectMetaMemoryManager


class LaunchCrewConfig(BaseModel):
    """Configuration for the Launch Crew."""
    
    enable_memory_learning: bool = Field(default=True, description="Enable memory learning")
    enable_launch_preparation: bool = Field(default=True, description="Enable launch preparation")
    max_launch_iterations: int = Field(default=3, description="Maximum launch iterations")
    enable_post_launch_analysis: bool = Field(default=True, description="Enable post-launch analysis")
    enable_crisis_management: bool = Field(default=True, description="Enable crisis management")


@CrewBase
class LaunchCrew:
    """Launch Crew for comprehensive launch preparation and execution."""
    
    def __init__(self, config: Optional[LaunchCrewConfig] = None):
        """Initialize the Launch Crew."""
        self.config = config or LaunchCrewConfig()
        self.memory_manager = ProjectMetaMemoryManager()
        self.launch_agent = LaunchAgent()
        
    @agent
    def launch_preparer(self) -> LaunchAgent:
        """Launch preparation agent for comprehensive launch planning."""
        return self.launch_agent
    
    @agent
    def execution_coordinator(self) -> LaunchAgent:
        """Execution coordinator agent for launch day activities."""
        return LaunchAgent()
    
    @agent
    def post_launch_analyst(self) -> LaunchAgent:
        """Post-launch analyst agent for performance analysis."""
        return LaunchAgent()
    
    @agent
    def crisis_manager(self) -> LaunchAgent:
        """Crisis manager agent for handling launch issues."""
        return LaunchAgent()
    
    @agent
    def momentum_builder(self) -> LaunchAgent:
        """Momentum builder agent for sustaining launch success."""
        return LaunchAgent()

    @task
    def comprehensive_launch_preparation(self) -> Task:
        """Prepare comprehensive launch strategy and checklist."""
        return Task(
            description="""
            Prepare comprehensive launch strategy and execution checklist.
            
            Prepare:
            1. Launch timeline and milestone planning
            2. Pre-launch marketing and buzz building
            3. Technical deployment and infrastructure readiness
            4. Team coordination and communication plan
            5. Crisis management and contingency planning
            
            Provide detailed launch preparation with execution checklist.
            """,
            agent=self.launch_preparer(),
            expected_output="Comprehensive launch preparation with execution checklist."
        )

    @task
    def launch_day_execution(self) -> Task:
        """Execute launch day activities and coordination."""
        return Task(
            description="""
            Execute launch day activities and coordinate all launch efforts.
            
            Execute:
            1. Launch day timeline and milestone execution
            2. Real-time monitoring and issue resolution
            3. Team coordination and communication
            4. Customer support and feedback collection
            5. Performance monitoring and optimization
            
            Provide launch day execution report with key metrics.
            """,
            agent=self.execution_coordinator(),
            expected_output="Launch day execution report with performance metrics.",
            context=["comprehensive_launch_preparation"]
        )

    @task
    def post_launch_analysis(self) -> Task:
        """Analyze launch performance and gather insights."""
        return Task(
            description="""
            Analyze launch performance and gather comprehensive insights.
            
            Analyze:
            1. Launch day performance metrics
            2. User acquisition and engagement data
            3. Technical performance and stability
            4. Customer feedback and satisfaction
            5. Market response and competitive analysis
            
            Provide detailed post-launch analysis with actionable insights.
            """,
            agent=self.post_launch_analyst(),
            expected_output="Comprehensive post-launch analysis with insights and recommendations.",
            context=["launch_day_execution"]
        )

    @task
    def crisis_management_planning(self) -> Task:
        """Plan crisis management and issue resolution strategies."""
        return Task(
            description="""
            Plan crisis management and issue resolution strategies.
            
            Plan:
            1. Potential crisis scenarios and responses
            2. Communication protocols and messaging
            3. Escalation procedures and decision-making
            4. Recovery strategies and contingency plans
            5. Learning and improvement processes
            
            Provide crisis management framework with response protocols.
            """,
            agent=self.crisis_manager(),
            expected_output="Crisis management framework with response protocols.",
            context=["comprehensive_launch_preparation"]
        )

    @task
    def momentum_sustaining_strategy(self) -> Task:
        """Develop strategies to sustain launch momentum."""
        return Task(
            description="""
            Develop strategies to sustain launch momentum and growth.
            
            Develop:
            1. Post-launch marketing and growth strategies
            2. User retention and engagement programs
            3. Feature development and iteration planning
            4. Community building and advocacy programs
            5. Long-term success metrics and monitoring
            
            Provide momentum sustaining strategy with growth roadmap.
            """,
            agent=self.momentum_builder(),
            expected_output="Momentum sustaining strategy with growth roadmap.",
            context=["post_launch_analysis", "crisis_management_planning"]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Launch Crew."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )

    async def prepare_launch(self, product_info: Dict[str, Any], launch_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Prepare comprehensive launch strategy and checklist.
        
        Args:
            product_info: Product information and features
            launch_context: Launch context and requirements
            
        Returns:
            Launch preparation and strategy
        """
        # Store launch preparation in memory
        self.memory_manager.add_success_pattern(
            pattern={"launch_preparation": {"product_info": product_info, "context": launch_context}},
            project_id="launch_crew",
            agent_id="launch_crew",
            confidence_score=0.8
        )
        
        # Execute launch preparation
        inputs = {
            "product_info": product_info,
            "launch_context": launch_context or {},
            "preparation_type": "comprehensive_launch"
        }
        
        result = await self.crew().kickoff(inputs=inputs)
        
        return {
            "launch_timeline": result.get("launch_timeline", {}),
            "pre_launch_activities": result.get("pre_launch_activities", []),
            "launch_day_plan": result.get("launch_day_plan", {}),
            "post_launch_strategy": result.get("post_launch_strategy", {}),
            "crisis_management": result.get("crisis_management", {}),
            "success_metrics": result.get("success_metrics", [])
        }

    async def execute_launch(self, launch_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute launch day activities and coordination.
        
        Args:
            launch_plan: Launch plan and checklist
            
        Returns:
            Launch execution results and metrics
        """
        # Store launch execution in memory
        self.memory_manager.add_success_pattern(
            pattern={"launch_execution": launch_plan},
            project_id="launch_crew",
            agent_id="launch_crew",
            confidence_score=0.8
        )
        
        # Execute launch activities
        inputs = {
            "launch_plan": launch_plan,
            "execution_type": "launch_day"
        }
        
        result = await self.crew().kickoff(inputs=inputs)
        
        return {
            "launch_metrics": result.get("launch_metrics", {}),
            "user_acquisition": result.get("user_acquisition", {}),
            "technical_performance": result.get("technical_performance", {}),
            "customer_feedback": result.get("customer_feedback", {}),
            "issues_resolved": result.get("issues_resolved", []),
            "next_steps": result.get("next_steps", [])
        }

    async def analyze_launch_performance(self, launch_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze launch performance and provide insights.
        
        Args:
            launch_data: Launch execution data and metrics
            
        Returns:
            Performance analysis and recommendations
        """
        # Store performance analysis in memory
        self.memory_manager.add_success_pattern(
            pattern={"performance_analysis": launch_data},
            project_id="launch_crew",
            agent_id="launch_crew",
            confidence_score=0.8
        )
        
        # Execute performance analysis
        inputs = {
            "launch_data": launch_data,
            "analysis_type": "post_launch_performance"
        }
        
        result = await self.crew().kickoff(inputs=inputs)
        
        return {
            "performance_summary": result.get("performance_summary", {}),
            "key_insights": result.get("key_insights", []),
            "improvement_areas": result.get("improvement_areas", []),
            "success_metrics": result.get("success_metrics", {}),
            "recommendations": result.get("recommendations", []),
            "next_phase_planning": result.get("next_phase_planning", {})
        }

    async def run_async(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the launch crew asynchronously.
        
        Args:
            project_data: Project data to process
            
        Returns:
            Launch preparation and strategy
        """
        try:
            # Extract product info from project data
            product_info = {
                "idea": project_data.get('idea', ''),
                "validation": project_data.get('validation', {}),
                "marketing_assets": project_data.get('marketing_assets', {})
            }
            
            # Prepare launch strategy
            launch_preparation = await self.prepare_launch(product_info)
            
            # Execute launch (simulated for now)
            launch_execution = await self.execute_launch(launch_preparation)
            
            # Analyze performance
            performance_analysis = await self.analyze_launch_performance(launch_execution)
            
            # Combine results
            result = {
                "launch_preparation": launch_preparation,
                "launch_execution": launch_execution,
                "performance_analysis": performance_analysis,
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