"""
Comprehensive pricing system for LLM providers.
Provides accurate cost calculations and token counting.
"""

from dataclasses import dataclass
from typing import Dict, Any, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class Price:
    """Price information for a model."""
    model: str
    provider: str
    input_price_per_1k: float  # USD per 1000 input tokens
    output_price_per_1k: float  # USD per 1000 output tokens
    max_tokens: int = 128000  # Maximum context length
    description: str = ""

class PricingTable:
    """Comprehensive pricing table for LLM providers."""
    
    def __init__(self):
        """Initialize pricing table with current rates."""
        self.prices = self._load_prices()
    
    def _load_prices(self) -> Dict[str, Price]:
        """Load current pricing information."""
        return {
            # OpenAI Models
            "gpt-4o-mini": Price(
                model="gpt-4o-mini",
                provider="openai",
                input_price_per_1k=0.00015,
                output_price_per_1k=0.0006,
                max_tokens=128000,
                description="Fastest and most affordable GPT-4 model"
            ),
            "gpt-4o": Price(
                model="gpt-4o",
                provider="openai",
                input_price_per_1k=0.0025,
                output_price_per_1k=0.01,
                max_tokens=128000,
                description="Most capable GPT-4 model"
            ),
            "gpt-4": Price(
                model="gpt-4",
                provider="openai",
                input_price_per_1k=0.03,
                output_price_per_1k=0.06,
                max_tokens=8192,
                description="Legacy GPT-4 model"
            ),
            "gpt-3.5-turbo": Price(
                model="gpt-3.5-turbo",
                provider="openai",
                input_price_per_1k=0.0005,
                output_price_per_1k=0.0015,
                max_tokens=16385,
                description="Fast and cost-effective GPT-3.5 model"
            ),
            
            # Anthropic Models
            "claude-3-sonnet": Price(
                model="claude-3-sonnet",
                provider="anthropic",
                input_price_per_1k=0.003,
                output_price_per_1k=0.015,
                max_tokens=200000,
                description="Balanced Claude 3 model"
            ),
            "claude-3-haiku": Price(
                model="claude-3-haiku",
                provider="anthropic",
                input_price_per_1k=0.00025,
                output_price_per_1k=0.00125,
                max_tokens=200000,
                description="Fastest Claude 3 model"
            ),
            "claude-3-opus": Price(
                model="claude-3-opus",
                provider="anthropic",
                input_price_per_1k=0.015,
                output_price_per_1k=0.075,
                max_tokens=200000,
                description="Most capable Claude 3 model"
            ),
            
            # Local Models (free)
            "llama3.1:8b": Price(
                model="llama3.1:8b",
                provider="ollama",
                input_price_per_1k=0.0,
                output_price_per_1k=0.0,
                max_tokens=8192,
                description="Local Llama 3.1 8B model"
            ),
            "llama3.1:70b": Price(
                model="llama3.1:70b",
                provider="ollama",
                input_price_per_1k=0.0,
                output_price_per_1k=0.0,
                max_tokens=8192,
                description="Local Llama 3.1 70B model"
            ),
            
            # Groq Models (OpenAI-compatible)
            "llama3.1-8b-instant": Price(
                model="llama3.1-8b-instant",
                provider="groq",
                input_price_per_1k=0.00005,
                output_price_per_1k=0.0001,
                max_tokens=8192,
                description="Ultra-fast Llama 3.1 8B on Groq"
            ),
            "llama3.1-70b-version": Price(
                model="llama3.1-70b-version",
                provider="groq",
                input_price_per_1k=0.0007,
                output_price_per_1k=0.0008,
                max_tokens=8192,
                description="Fast Llama 3.1 70B on Groq"
            ),
            
            # Together AI Models
            "togethercomputer/llama-3.1-8b-instruct": Price(
                model="togethercomputer/llama-3.1-8b-instruct",
                provider="together",
                input_price_per_1k=0.0002,
                output_price_per_1k=0.0002,
                max_tokens=8192,
                description="Llama 3.1 8B on Together AI"
            ),
        }
    
    def get_price(self, model: str) -> Optional[Price]:
        """
        Get price information for a model.
        
        Args:
            model: Model name
            
        Returns:
            Price object or None if not found
        """
        return self.prices.get(model.lower())
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost for token usage.
        
        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Cost in USD
        """
        price = self.get_price(model)
        if not price:
            logger.warning(f"No pricing information for model: {model}")
            return 0.0
        
        input_cost = (input_tokens / 1000) * price.input_price_per_1k
        output_cost = (output_tokens / 1000) * price.output_price_per_1k
        
        return input_cost + output_cost
    
    def get_token_info(self, model: str) -> Tuple[int, int, float]:
        """
        Get token information for a model.
        
        Args:
            model: Model name
            
        Returns:
            Tuple of (input_tokens, output_tokens, cost_usd) for 1k tokens each
        """
        price = self.get_price(model)
        if not price:
            return (0, 0, 0.0)
        
        return (1000, 1000, price.input_price_per_1k + price.output_price_per_1k)
    
    def list_models(self, provider: Optional[str] = None) -> Dict[str, Price]:
        """
        List all available models.
        
        Args:
            provider: Optional provider filter
            
        Returns:
            Dictionary of model names to Price objects
        """
        if provider:
            return {
                name: price for name, price in self.prices.items()
                if price.provider.lower() == provider.lower()
            }
        return self.prices.copy()
    
    def get_cheapest_model(self, min_tokens: int = 0) -> Optional[Price]:
        """
        Get the cheapest model that meets minimum token requirements.
        
        Args:
            min_tokens: Minimum context length required
            
        Returns:
            Cheapest Price object or None
        """
        valid_models = [
            price for price in self.prices.values()
            if price.max_tokens >= min_tokens
        ]
        
        if not valid_models:
            return None
        
        # Sort by total cost for 1k input + 1k output tokens
        return min(valid_models, key=lambda p: p.input_price_per_1k + p.output_price_per_1k)
    
    def get_fastest_model(self, max_cost_per_1k: float = float('inf')) -> Optional[Price]:
        """
        Get the fastest model within cost constraints.
        
        Args:
            max_cost_per_1k: Maximum cost per 1k tokens (input + output)
            
        Returns:
            Fastest Price object or None
        """
        valid_models = [
            price for price in self.prices.values()
            if (price.input_price_per_1k + price.output_price_per_1k) <= max_cost_per_1k
        ]
        
        if not valid_models:
            return None
        
        # For now, assume local models are fastest, then by provider
        # This is a simplified heuristic - in practice you'd want actual latency data
        def speed_score(price: Price) -> int:
            if price.provider == "ollama":
                return 0  # Local models are fastest
            elif price.provider == "groq":
                return 1  # Groq is very fast
            elif price.provider == "together":
                return 2  # Together is fast
            elif price.provider == "openai":
                return 3  # OpenAI is standard
            elif price.provider == "anthropic":
                return 4  # Anthropic can be slower
            else:
                return 5
        
        return min(valid_models, key=speed_score)

# Global pricing table instance
pricing_table = PricingTable()

def calculate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    """
    Calculate cost in USD for token usage.
    
    Args:
        model: Model name
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        
    Returns:
        Cost in USD
    """
    return pricing_table.calculate_cost(model, input_tokens, output_tokens)

def get_model_info(model: str) -> Optional[Price]:
    """
    Get model information including pricing.
    
    Args:
        model: Model name
        
    Returns:
        Price object or None
    """
    return pricing_table.get_price(model)
