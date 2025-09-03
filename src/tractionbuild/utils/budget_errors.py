"""
Budget error classes for proper error handling and budget enforcement.
"""

class BudgetError(Exception):
    """Base class for budget-related errors."""
    
    def __init__(self, message: str, scope: str = "global", cost_usd: float = 0.0):
        self.message = message
        self.scope = scope
        self.cost_usd = cost_usd
        super().__init__(self.message)

class DailyBudgetExceededError(BudgetError):
    """Raised when daily budget is exceeded."""
    
    def __init__(self, scope: str, cost_usd: float, daily_budget: float, daily_usage: float):
        message = f"Daily budget exceeded for scope '{scope}': ${daily_usage + cost_usd:.2f} > ${daily_budget}"
        super().__init__(message, scope, cost_usd)
        self.daily_budget = daily_budget
        self.daily_usage = daily_usage

class MonthlyBudgetExceededError(BudgetError):
    """Raised when monthly budget is exceeded."""
    
    def __init__(self, scope: str, cost_usd: float, monthly_budget: float, monthly_usage: float):
        message = f"Monthly budget exceeded for scope '{scope}': ${monthly_usage + cost_usd:.2f} > ${monthly_budget}"
        super().__init__(message, scope, cost_usd)
        self.monthly_budget = monthly_budget
        self.monthly_usage = monthly_usage

class RateLimitExceededError(BudgetError):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, scope: str, tokens_requested: int, rate_limit: int, window_seconds: int):
        message = f"Rate limit exceeded for scope '{scope}': {tokens_requested} tokens > {rate_limit} per {window_seconds}s"
        super().__init__(message, scope, 0.0)
        self.tokens_requested = tokens_requested
        self.rate_limit = rate_limit
        self.window_seconds = window_seconds

class BudgetConfigurationError(BudgetError):
    """Raised when budget configuration is invalid."""
    
    def __init__(self, scope: str, message: str):
        super().__init__(f"Budget configuration error for scope '{scope}': {message}", scope, 0.0)
