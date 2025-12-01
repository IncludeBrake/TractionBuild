"""
Launch Agent for tractionbuild.
Specialized agent for launch preparation, execution, and analysis.
"""

from typing import Dict, List, Optional, Any
from crewai import Agent
from pydantic import BaseModel, Field


class LaunchAgentConfig(BaseModel):
    """Configuration for the Launch Agent."""
    
    enable_launch_planning: bool = Field(default=True, description="Enable launch planning")
    enable_execution_coordination: bool = Field(default=True, description="Enable execution coordination")
    enable_performance_analysis: bool = Field(default=True, description="Enable performance analysis")
    enable_crisis_management: bool = Field(default=True, description="Enable crisis management")


class LaunchAgent:
    """Launch Agent for comprehensive launch activities."""
    
    def __init__(self, config: Optional[LaunchAgentConfig] = None):
        """Initialize the Launch Agent."""
        self.config = config or LaunchAgentConfig()
        
    def create_agent(self, role: str, goal: str, backstory: str) -> Agent:
        """
        Create a launch agent with specific role and capabilities.
        
        Args:
            role: Agent role and responsibilities
            goal: Agent goal and objectives
            backstory: Agent background and expertise
            
        Returns:
            Configured launch agent
        """
        return Agent(
            role=role,
            goal=goal,
            backstory=backstory,
            verbose=True,
            allow_delegation=False
        )
    
    def launch_preparer_agent(self) -> Agent:
        """Create launch preparation agent."""
        return self.create_agent(
            role="Launch Preparation Specialist",
            goal="Prepare comprehensive launch strategies and execution plans",
            backstory="""You are an expert launch preparation specialist with extensive experience 
            in product launches across various industries. You excel at creating detailed launch 
            timelines, coordinating cross-functional teams, and developing crisis management plans. 
            Your expertise includes pre-launch marketing, technical deployment readiness, and 
            post-launch success measurement."""
        )
    
    def execution_coordinator_agent(self) -> Agent:
        """Create launch execution coordinator agent."""
        return self.create_agent(
            role="Launch Execution Coordinator",
            goal="Coordinate and execute launch day activities successfully",
            backstory="""You are a seasoned launch execution coordinator with a proven track record 
            of managing successful product launches. You excel at real-time coordination, issue 
            resolution, and maintaining launch momentum. Your expertise includes team coordination, 
            customer support management, and performance monitoring during critical launch periods."""
        )
    
    def post_launch_analyst_agent(self) -> Agent:
        """Create post-launch analysis agent."""
        return self.create_agent(
            role="Post-Launch Performance Analyst",
            goal="Analyze launch performance and provide actionable insights",
            backstory="""You are a data-driven post-launch analyst with deep expertise in 
            performance measurement and optimization. You excel at analyzing launch metrics, 
            identifying improvement opportunities, and providing strategic recommendations. 
            Your expertise includes user acquisition analysis, engagement metrics, and 
            competitive performance benchmarking."""
        )
    
    def crisis_manager_agent(self) -> Agent:
        """Create crisis management agent."""
        return self.create_agent(
            role="Launch Crisis Manager",
            goal="Develop and execute crisis management strategies",
            backstory="""You are an experienced crisis management specialist with expertise in 
            handling launch-related issues and emergencies. You excel at developing contingency 
            plans, managing communication during crises, and implementing recovery strategies. 
            Your expertise includes risk assessment, communication protocols, and stakeholder 
            management during critical situations."""
        )
    
    def momentum_builder_agent(self) -> Agent:
        """Create momentum building agent."""
        return self.create_agent(
            role="Launch Momentum Builder",
            goal="Develop strategies to sustain and build launch momentum",
            backstory="""You are a strategic momentum builder with expertise in sustaining 
            launch success and driving long-term growth. You excel at developing post-launch 
            strategies, building user communities, and creating sustainable growth programs. 
            Your expertise includes user retention strategies, community building, and 
            long-term success planning."""
        ) 