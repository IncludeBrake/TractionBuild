"""
Token budget management for ZeroToShip.
Controls per-crew and global token usage with safety limits.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import logging

from pydantic import BaseModel, Field


class BudgetLevel(str, Enum):
    """Token budget levels."""
    PER_AGENT = "per_agent"
    PER_CREW = "per_crew"
    PER_RUN = "per_run"
    PER_PROJECT = "per_project"
    GLOBAL = "global"


class BudgetAction(str, Enum):
    """Actions when budget is exceeded."""
    CONTINUE = "continue"
    WARN = "warn"
    HALT = "halt"
    THROTTLE = "throttle"
    FAIL = "fail"


@dataclass
class TokenUsage:
    """Token usage tracking."""
    agent_id: str
    crew_id: str
    project_id: str
    tokens_used: int
    timestamp: datetime
    model: str
    cost_estimate: float = 0.0


@dataclass
class BudgetLimit:
    """Budget limit configuration."""
    level: BudgetLevel
    max_tokens: int
    action: BudgetAction = BudgetAction.WARN
    reset_interval: Optional[timedelta] = None
    last_reset: Optional[datetime] = None


class TokenBudgetManager(BaseModel):
    """Token budget manager for cost control and safety."""
    
    # Budget limits
    per_agent_limit: int = Field(default=10000, description="Max tokens per agent")
    per_crew_limit: int = Field(default=50000, description="Max tokens per crew")
    per_run_limit: int = Field(default=200000, description="Max tokens per run")
    per_project_limit: int = Field(default=1000000, description="Max tokens per project")
    global_daily_limit: int = Field(default=10000000, description="Max tokens per day globally")
    
    # Safety settings
    enable_budgeting: bool = Field(default=True, description="Enable token budgeting")
    enable_cost_tracking: bool = Field(default=True, description="Enable cost tracking")
    enable_throttling: bool = Field(default=True, description="Enable throttling")
    
    # Cost estimates (per 1K tokens)
    cost_estimates: Dict[str, float] = Field(
        default={
            "gpt-4-turbo-preview": 0.03,
            "gpt-4": 0.06,
            "gpt-3.5-turbo": 0.002,
            "claude-3-sonnet": 0.015,
            "claude-3-haiku": 0.00025
        },
        description="Cost estimates per 1K tokens"
    )
    
    # Runtime state (not serialized)
    usage_history: List[TokenUsage] = Field(default_factory=list, exclude=True)
    budget_limits: Dict[str, BudgetLimit] = Field(default_factory=dict, exclude=True)
    logger: Optional[Any] = Field(default=None, exclude=True)
    
    def __init__(self, **data):
        """Initialize the token budget manager."""
        super().__init__(**data)
        self._setup_default_limits()
        self.logger = logging.getLogger(__name__)
    
    def _setup_default_limits(self):
        """Setup default budget limits."""
        self.budget_limits = {
            BudgetLevel.PER_AGENT: BudgetLimit(
                level=BudgetLevel.PER_AGENT,
                max_tokens=self.per_agent_limit,
                action=BudgetAction.WARN
            ),
            BudgetLevel.PER_CREW: BudgetLimit(
                level=BudgetLevel.PER_CREW,
                max_tokens=self.per_crew_limit,
                action=BudgetAction.HALT
            ),
            BudgetLevel.PER_RUN: BudgetLimit(
                level=BudgetLevel.PER_RUN,
                max_tokens=self.per_run_limit,
                action=BudgetAction.FAIL
            ),
            BudgetLevel.PER_PROJECT: BudgetLimit(
                level=BudgetLevel.PER_PROJECT,
                max_tokens=self.per_project_limit,
                action=BudgetAction.THROTTLE
            ),
            BudgetLevel.GLOBAL: BudgetLimit(
                level=BudgetLevel.GLOBAL,
                max_tokens=self.global_daily_limit,
                action=BudgetAction.FAIL,
                reset_interval=timedelta(days=1)
            )
        }
    
    async def check_budget(
        self,
        agent_id: str,
        crew_id: str,
        project_id: str,
        estimated_tokens: int,
        model: str = "gpt-4-turbo-preview"
    ) -> Dict[str, Any]:
        """
        Check if token usage is within budget limits.
        
        Args:
            agent_id: Agent identifier
            crew_id: Crew identifier
            project_id: Project identifier
            estimated_tokens: Estimated tokens to use
            model: Model being used
            
        Returns:
            Budget check result
        """
        if not self.enable_budgeting:
            return {"allowed": True, "reason": "Budgeting disabled"}
        
        # Check each budget level
        for level, limit in self.budget_limits.items():
            current_usage = await self._get_current_usage(level, agent_id, crew_id, project_id)
            projected_usage = current_usage + estimated_tokens
            
            if projected_usage > limit.max_tokens:
                return await self._handle_budget_exceeded(
                    level, limit, current_usage, projected_usage, estimated_tokens
                )
        
        return {"allowed": True, "reason": "Within budget limits"}
    
    async def record_usage(
        self,
        agent_id: str,
        crew_id: str,
        project_id: str,
        tokens_used: int,
        model: str = "gpt-4-turbo-preview"
    ) -> None:
        """
        Record token usage.
        
        Args:
            agent_id: Agent identifier
            crew_id: Crew identifier
            project_id: Project identifier
            tokens_used: Tokens actually used
            model: Model used
        """
        cost_estimate = self._calculate_cost(tokens_used, model)
        
        usage = TokenUsage(
            agent_id=agent_id,
            crew_id=crew_id,
            project_id=project_id,
            tokens_used=tokens_used,
            timestamp=datetime.now(),
            model=model,
            cost_estimate=cost_estimate
        )
        
        self.usage_history.append(usage)
        self.logger.info(f"Recorded usage: {tokens_used} tokens, ${cost_estimate:.4f}")
    
    async def get_usage_summary(
        self,
        project_id: Optional[str] = None,
        crew_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        time_window: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """
        Get usage summary for specified filters.
        
        Args:
            project_id: Optional project filter
            crew_id: Optional crew filter
            agent_id: Optional agent filter
            time_window: Optional time window
            
        Returns:
            Usage summary
        """
        filtered_usage = self._filter_usage(project_id, crew_id, agent_id, time_window)
        
        total_tokens = sum(u.tokens_used for u in filtered_usage)
        total_cost = sum(u.cost_estimate for u in filtered_usage)
        
        return {
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "usage_count": len(filtered_usage),
            "time_window": time_window,
            "filters": {
                "project_id": project_id,
                "crew_id": crew_id,
                "agent_id": agent_id
            }
        }
    
    async def _get_current_usage(
        self,
        level: BudgetLevel,
        agent_id: str,
        crew_id: str,
        project_id: str
    ) -> int:
        """Get current usage for a specific budget level."""
        now = datetime.now()
        limit = self.budget_limits[level]
        
        # Apply reset interval if specified
        if limit.reset_interval and limit.last_reset:
            if now - limit.last_reset > limit.reset_interval:
                return 0
        
        # Filter usage based on level
        if level == BudgetLevel.PER_AGENT:
            return sum(u.tokens_used for u in self.usage_history 
                      if u.agent_id == agent_id)
        elif level == BudgetLevel.PER_CREW:
            return sum(u.tokens_used for u in self.usage_history 
                      if u.crew_id == crew_id)
        elif level == BudgetLevel.PER_RUN:
            # For per-run, we only count recent usage (last 1 hour)
            recent_cutoff = now - timedelta(hours=1)
            return sum(u.tokens_used for u in self.usage_history 
                      if u.timestamp > recent_cutoff)
        elif level == BudgetLevel.PER_PROJECT:
            return sum(u.tokens_used for u in self.usage_history 
                      if u.project_id == project_id)
        elif level == BudgetLevel.GLOBAL:
            # For global, we count daily usage
            daily_cutoff = now - timedelta(days=1)
            return sum(u.tokens_used for u in self.usage_history 
                      if u.timestamp > daily_cutoff)
        
        return 0
    
    async def _handle_budget_exceeded(
        self,
        level: BudgetLevel,
        limit: BudgetLimit,
        current_usage: int,
        projected_usage: int,
        estimated_tokens: int
    ) -> Dict[str, Any]:
        """Handle budget exceeded scenario."""
        self.logger.warning(
            f"Budget exceeded: {level} limit {limit.max_tokens}, "
            f"current {current_usage}, projected {projected_usage}"
        )
        
        if limit.action == BudgetAction.CONTINUE:
            return {"allowed": True, "reason": f"{level} exceeded but continuing"}
        
        elif limit.action == BudgetAction.WARN:
            self.logger.warning(f"Token budget warning: {level}")
            return {"allowed": True, "reason": f"{level} exceeded with warning"}
        
        elif limit.action == BudgetAction.HALT:
            return {
                "allowed": False,
                "reason": f"{level} budget exceeded, halting execution",
                "level": level,
                "current_usage": current_usage,
                "limit": limit.max_tokens
            }
        
        elif limit.action == BudgetAction.THROTTLE:
            # Calculate reduced token allocation
            available_tokens = max(0, limit.max_tokens - current_usage)
            return {
                "allowed": True,
                "reason": f"{level} exceeded, throttling to {available_tokens} tokens",
                "throttled_tokens": available_tokens
            }
        
        elif limit.action == BudgetAction.FAIL:
            return {
                "allowed": False,
                "reason": f"{level} budget exceeded, failing execution",
                "level": level,
                "current_usage": current_usage,
                "limit": limit.max_tokens
            }
        
        return {"allowed": False, "reason": f"Unknown action for {level}"}
    
    def _calculate_cost(self, tokens: int, model: str) -> float:
        """Calculate estimated cost for token usage."""
        if not self.enable_cost_tracking:
            return 0.0
        
        cost_per_1k = self.cost_estimates.get(model, 0.03)  # Default to GPT-4 pricing
        return (tokens / 1000) * cost_per_1k
    
    def _filter_usage(
        self,
        project_id: Optional[str] = None,
        crew_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        time_window: Optional[timedelta] = None
    ) -> List[TokenUsage]:
        """Filter usage history based on criteria."""
        filtered = self.usage_history
        
        if project_id:
            filtered = [u for u in filtered if u.project_id == project_id]
        
        if crew_id:
            filtered = [u for u in filtered if u.crew_id == crew_id]
        
        if agent_id:
            filtered = [u for u in filtered if u.agent_id == agent_id]
        
        if time_window:
            cutoff = datetime.now() - time_window
            filtered = [u for u in filtered if u.timestamp > cutoff]
        
        return filtered
    
    def reset_budget(self, level: BudgetLevel) -> None:
        """Reset budget for a specific level."""
        if level in self.budget_limits:
            self.budget_limits[level].last_reset = datetime.now()
            self.logger.info(f"Reset budget for {level}")
    
    def update_budget_limit(
        self,
        level: BudgetLevel,
        max_tokens: int,
        action: BudgetAction = BudgetAction.WARN
    ) -> None:
        """Update budget limit for a specific level."""
        if level in self.budget_limits:
            self.budget_limits[level].max_tokens = max_tokens
            self.budget_limits[level].action = action
            self.logger.info(f"Updated budget limit for {level}: {max_tokens} tokens") 