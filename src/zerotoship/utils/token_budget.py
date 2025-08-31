"""
Token Budget Management for ZeroToShip.
Provides cost control and monitoring for LLM usage.
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class TokenUsage:
    """Token usage statistics for cost tracking."""
    tokens_used: int = 0
    cost_usd: float = 0.0
    requests_made: int = 0
    cache_hits: int = 0
    last_reset: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class TokenBudgetManager:
    """Manages token budgets and cost control for LLM usage."""
    
    def __init__(self, 
                 daily_budget_usd: float = 10.0,
                 monthly_budget_usd: float = 100.0,
                 cost_per_1k_tokens: float = 0.01):
        """
        Initialize the token budget manager.
        
        Args:
            daily_budget_usd: Daily budget in USD
            monthly_budget_usd: Monthly budget in USD  
            cost_per_1k_tokens: Cost per 1000 tokens in USD
        """
        self.daily_budget_usd = daily_budget_usd
        self.monthly_budget_usd = monthly_budget_usd
        self.cost_per_1k_tokens = cost_per_1k_tokens
        
        # Load existing usage data
        self.usage_file = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'token_usage.json')
        self.usage = self._load_usage()
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.usage_file), exist_ok=True)
    
    def _load_usage(self) -> Dict[str, TokenUsage]:
        """Load usage data from file."""
        try:
            if os.path.exists(self.usage_file):
                with open(self.usage_file, 'r') as f:
                    data = json.load(f)
                    return {
                        date: TokenUsage(**usage_data) 
                        for date, usage_data in data.items()
                    }
        except Exception as e:
            logger.warning(f"Failed to load usage data: {e}")
        
        return {}
    
    def _save_usage(self):
        """Save usage data to file."""
        try:
            data = {
                date: usage.to_dict() 
                for date, usage in self.usage.items()
            }
            with open(self.usage_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save usage data: {e}")
    
    def _get_today_key(self) -> str:
        """Get today's date key."""
        return datetime.now().strftime("%Y-%m-%d")
    
    def _get_month_key(self) -> str:
        """Get current month key."""
        return datetime.now().strftime("%Y-%m")
    
    def record_usage(self, 
                    tokens_used: int, 
                    is_cache_hit: bool = False,
                    model: str = "unknown") -> bool:
        """
        Record token usage and check budget limits.
        
        Args:
            tokens_used: Number of tokens used
            is_cache_hit: Whether this was a cache hit
            model: Model name for cost calculation
            
        Returns:
            True if within budget, False if budget exceeded
        """
        today = self._get_today_key()
        month = self._get_month_key()
        
        # Initialize usage records if needed
        if today not in self.usage:
            self.usage[today] = TokenUsage(last_reset=today)
        if month not in self.usage:
            self.usage[month] = TokenUsage(last_reset=month)
        
        # Calculate cost (adjust based on model)
        cost_multiplier = self._get_cost_multiplier(model)
        cost = (tokens_used / 1000) * self.cost_per_1k_tokens * cost_multiplier
        
        # Update usage
        if not is_cache_hit:
            self.usage[today].tokens_used += tokens_used
            self.usage[today].cost_usd += cost
            self.usage[today].requests_made += 1
            
            self.usage[month].tokens_used += tokens_used
            self.usage[month].cost_usd += cost
            self.usage[month].requests_made += 1
        else:
            self.usage[today].cache_hits += 1
            self.usage[month].cache_hits += 1
        
        # Check budget limits
        daily_exceeded = self.usage[today].cost_usd > self.daily_budget_usd
        monthly_exceeded = self.usage[month].cost_usd > self.monthly_budget_usd
        
        if daily_exceeded:
            logger.warning(f"Daily budget exceeded: ${self.usage[today].cost_usd:.2f} > ${self.daily_budget_usd}")
        
        if monthly_exceeded:
            logger.warning(f"Monthly budget exceeded: ${self.usage[month].cost_usd:.2f} > ${self.monthly_budget_usd}")
        
        # Save usage data
        self._save_usage()
        
        return not (daily_exceeded or monthly_exceeded)
    
    def _get_cost_multiplier(self, model: str) -> float:
        """Get cost multiplier based on model."""
        # Cost multipliers relative to GPT-4o-mini
        multipliers = {
            "gpt-4o-mini": 1.0,
            "gpt-4o": 2.0,
            "gpt-4": 3.0,
            "gpt-3.5-turbo": 0.5,
            "claude-3-sonnet": 1.5,
            "claude-3-haiku": 0.3,
            "llama3.1:8b": 0.0,  # Local model, no cost
        }
        return multipliers.get(model.lower(), 1.0)
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get current usage summary."""
        today = self._get_today_key()
        month = self._get_month_key()
        
        today_usage = self.usage.get(today, TokenUsage())
        month_usage = self.usage.get(month, TokenUsage())
        
        return {
            "today": {
                "tokens_used": today_usage.tokens_used,
                "cost_usd": today_usage.cost_usd,
                "requests_made": today_usage.requests_made,
                "cache_hits": today_usage.cache_hits,
                "budget_remaining": max(0, self.daily_budget_usd - today_usage.cost_usd)
            },
            "month": {
                "tokens_used": month_usage.tokens_used,
                "cost_usd": month_usage.cost_usd,
                "requests_made": month_usage.requests_made,
                "cache_hits": month_usage.cache_hits,
                "budget_remaining": max(0, self.monthly_budget_usd - month_usage.cost_usd)
            },
            "budgets": {
                "daily_usd": self.daily_budget_usd,
                "monthly_usd": self.monthly_budget_usd
            }
        }
    
    def reset_usage(self, period: str = "today"):
        """Reset usage for specified period."""
        if period == "today":
            today = self._get_today_key()
            if today in self.usage:
                self.usage[today] = TokenUsage(last_reset=today)
        elif period == "month":
            month = self._get_month_key()
            if month in self.usage:
                self.usage[month] = TokenUsage(last_reset=month)
        
        self._save_usage()
        logger.info(f"Reset usage for {period}")

# Global instance
token_budget = TokenBudgetManager(
    daily_budget_usd=float(os.getenv("LLM_DAILY_BUDGET_USD", "10.0")),
    monthly_budget_usd=float(os.getenv("LLM_MONTHLY_BUDGET_USD", "100.0")),
    cost_per_1k_tokens=float(os.getenv("LLM_COST_PER_1K_TOKENS", "0.01"))
)
