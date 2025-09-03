"""
Marketing Agent for tractionbuild.
Generates marketing assets using Salem.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from crewai import Agent
from pydantic import BaseModel, Field

from ..tools.salem_marketing_tool import SalemMarketingTool

logger = logging.getLogger(__name__)

class MarketingAgentConfig(BaseModel):
    """Configuration for the Marketing Agent."""
    
    name: str = Field(default="Marketing Agent", description="Agent name")
    role: str = Field(default="Marketing Asset Generation", description="Agent role")
    goal: str = Field(
        default="Generate high-quality marketing assets using Salem",
        description="Agent goal"
    )
    backstory: str = Field(
        default="""You are an expert marketing strategist and copywriter with 15+ years 
        of experience in product launches, brand positioning, and growth marketing. 
        You have successfully launched hundreds of products and campaigns.""",
        description="Agent backstory"
    )
    verbose: bool = Field(default=True, description="Enable verbose logging")
    allow_delegation: bool = Field(default=False, description="Allow task delegation")
    max_iterations: int = Field(default=3, description="Maximum iterations for marketing")

class MarketingAgent:
    """Marketing Agent that generates marketing assets using Salem."""
    
    def __init__(self, config: Optional[MarketingAgentConfig] = None):
        """Initialize the Marketing Agent."""
        self.config = config or MarketingAgentConfig()
        self.tool = SalemMarketingTool()
        self.agent = self._create_agent()
    
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

    async def execute(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the marketing agent to generate marketing assets."""
        try:
            logger.info(f"Starting marketing agent for project {project_data.get('id', 'unknown')}")
            
            # Extract project information
            avatar = (project_data.get("target_avatars") or ["startup_entrepreneur"])[0]
            desc = project_data.get("hypothesis") or project_data.get("description") or project_data.get("name")
            
            # Generate marketing assets
            result = await self.tool._run(product_description=desc, avatar=avatar, hooks=3)
            
            logger.info(f"Marketing agent completed for project {project_data.get('id', 'unknown')}")
            
            return result["artifact"]  # normalized dict
            
        except Exception as e:
            logger.error(f"Marketing agent failed: {str(e)}")
            raise e 