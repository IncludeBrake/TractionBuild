# llm.py
import os
import requests
import json
import hashlib
import httpx
from functools import wraps

# --- Reading configuration from environment variables ---
# This determines which provider's logic to use below. Defaults to "openai".
PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()

# This sets the specific model name for the chosen provider.
MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

# Import new cache system
from .cache import cache_manager, generate_cache_key

# Import new budget store
try:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
    from tractionbuild.utils.budget_store import budget_store, UsageRecord
    from tractionbuild.utils.pricing import calculate_cost_usd
    from tractionbuild.utils.budget_errors import BudgetError, DailyBudgetExceededError, MonthlyBudgetExceededError
    BUDGET_SYSTEM_AVAILABLE = True
except ImportError:
    BUDGET_SYSTEM_AVAILABLE = False
    print("--- Budget system not available ---")

# Enhanced logging setup
import logging
logger = logging.getLogger(__name__)

def cache_result(func):
    @wraps(func)
    def wrapper(messages, **kwargs):
        # Generate versioned cache key with TTL
        key = generate_cache_key(messages, MODEL, **kwargs)
        
        # Check cache first
        cached_result = cache_manager.get(key)
        if cached_result is not None:
            logger.info("Returning response from cache for key: %s", key[:8] + "...")
            # Record cache hit if budget system is available
            if BUDGET_SYSTEM_AVAILABLE:
                record = UsageRecord(
                    scope="global",
                    model=MODEL,
                    tokens_input=0,
                    tokens_output=0,
                    cost_usd=0.0,
                    is_cache_hit=True,
                    provider=PROVIDER
                )
                budget_store.record_usage(record)
            return cached_result
        
        # If not in cache, call the original function and store the result
        result = func(messages, **kwargs)
        cache_manager.set(key, result, MODEL)
        return result
    return wrapper

@cache_result
def chat(messages, **kwargs):
    """
    A single, provider-agnostic function to interact with an LLM.
    It routes the request to the correct provider based on the LLM_PROVIDER
    environment variable.

    Args:
        messages (list): A list of message dictionaries, e.g., [{"role": "user", "content": "Hello"}]
        **kwargs: Additional keyword arguments to pass to the provider's API, like 'temperature'.

    Returns:
        str: The text content of the LLM's response.
    """
    logger.info("Routing to LLM Provider: %s, Model: %s", PROVIDER, MODEL)

    # --- Provider 1: OpenAI ---
    if PROVIDER == "openai":
        # You need to install the openai library: pip install openai
        from openai import OpenAI
        client = OpenAI() # The client automatically looks for the OPENAI_API_KEY env var
        
        # Check budget before making the call
        if BUDGET_SYSTEM_AVAILABLE:
            # Estimate cost based on input tokens (rough estimate)
            input_tokens = sum(len(msg.get("content", "").split()) * 1.3 for msg in messages)
            estimated_cost = calculate_cost_usd(MODEL, int(input_tokens), 0)
            
            # Create a temporary record to check budget
            temp_record = UsageRecord(
                scope="global",
                model=MODEL,
                tokens_input=int(input_tokens),
                tokens_output=0,
                cost_usd=estimated_cost,
                is_cache_hit=False,
                provider=PROVIDER
            )
            
            if not budget_store.record_usage(temp_record):
                raise BudgetError(f"Budget check failed for {MODEL}")
        
        try:
            response = client.chat.completions.create(model=MODEL, messages=messages, **kwargs)
            
            # Record actual usage
            if BUDGET_SYSTEM_AVAILABLE:
                input_tokens = response.usage.prompt_tokens if hasattr(response, 'usage') else 0
                output_tokens = response.usage.completion_tokens if hasattr(response, 'usage') else 0
                actual_cost = calculate_cost_usd(MODEL, input_tokens, output_tokens)
                
                record = UsageRecord(
                    scope="global",
                    model=MODEL,
                    tokens_input=input_tokens,
                    tokens_output=output_tokens,
                    cost_usd=actual_cost,
                    is_cache_hit=False,
                    provider=PROVIDER
                )
                budget_store.record_usage(record)
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise

    # --- Provider 2: OpenAI-Compatible (Groq, Together, Fireworks, etc.) ---
    if PROVIDER == "openai_compat":
        # No extra library needed, we use the 'requests' library: pip install requests
        url = os.getenv("OPENAI_COMPAT_BASE_URL") + "/v1/chat/completions"
        headers = {"Authorization": f"Bearer {os.getenv('OPENAI_COMPAT_API_KEY')}"}
        payload = {"model": MODEL, "messages": messages, **kwargs}

        # Make the API call
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status() # This will raise an error for bad responses (like 4xx or 5xx)

        response_data = response.json()
        
        # Track token usage if budget system is available
        if BUDGET_SYSTEM_AVAILABLE:
                tokens_used = response_data.get("usage", {}).get("total_tokens", 0)
                # Estimate input/output split (rough approximation)
                input_tokens = int(tokens_used * 0.7)
                output_tokens = tokens_used - input_tokens
                actual_cost = calculate_cost_usd(MODEL, input_tokens, output_tokens)
                
                record = UsageRecord(
                    scope="global",
                    model=MODEL,
                    tokens_input=input_tokens,
                    tokens_output=output_tokens,
                    cost_usd=actual_cost,
                    is_cache_hit=False,
                    provider=PROVIDER
                )
                budget_store.record_usage(record)

        return response_data["choices"][0]["message"]["content"]

    # --- Provider 3: Anthropic ---
    if PROVIDER == "anthropic":
        # You need to install the anthropic library: pip install anthropic
        import anthropic
        client = anthropic.Anthropic() # The client automatically looks for ANTHROPIC_API_KEY env var

        # Anthropic's API has a slightly different structure
        response = client.messages.create(model=MODEL, max_tokens=1024, messages=messages, **kwargs)
        
        # Track token usage if budget system is available
        if BUDGET_SYSTEM_AVAILABLE:
            input_tokens = response.usage.input_tokens if hasattr(response, 'usage') else 0
            output_tokens = response.usage.output_tokens if hasattr(response, 'usage') else 0
            actual_cost = calculate_cost_usd(MODEL, input_tokens, output_tokens)
            
            record = UsageRecord(
                scope="global",
                model=MODEL,
                tokens_input=input_tokens,
                tokens_output=output_tokens,
                cost_usd=actual_cost,
                is_cache_hit=False,
                provider=PROVIDER
            )
            budget_store.record_usage(record)
        
        return response.content[0].text

    # --- Error Handling ---
    raise ValueError(f"Unknown or unsupported LLM_PROVIDER: {PROVIDER}")


async def achat(messages, **kwargs):
    """
    Asynchronous version of the chat function for concurrent LLM calls.
    
    Args:
        messages (list): A list of message dictionaries, e.g., [{"role": "user", "content": "Hello"}]
        **kwargs: Additional keyword arguments to pass to the provider's API, like 'temperature'.

    Returns:
        str: The text content of the LLM's response.
    """
    logger.info("Async routing to LLM Provider: %s, Model: %s", PROVIDER, MODEL)

    # --- Provider 1: OpenAI (Async) ---
    if PROVIDER == "openai":
        try:
            # Requires: pip install "openai[async]"
            from openai import AsyncOpenAI
            client = AsyncOpenAI()
            response = await client.chat.completions.create(model=MODEL, messages=messages, **kwargs)
            
            # Track token usage if budget system is available
            if BUDGET_SYSTEM_AVAILABLE:
                input_tokens = response.usage.prompt_tokens if hasattr(response, 'usage') else 0
                output_tokens = response.usage.completion_tokens if hasattr(response, 'usage') else 0
                actual_cost = calculate_cost_usd(MODEL, input_tokens, output_tokens)
                
                record = UsageRecord(
                    scope="global",
                    model=MODEL,
                    tokens_input=input_tokens,
                    tokens_output=output_tokens,
                    cost_usd=actual_cost,
                    is_cache_hit=False,
                    provider=PROVIDER
                )
                budget_store.record_usage(record)
            
            return response.choices[0].message.content
        except ImportError:
            logger.error("Async OpenAI not available. Install with: pip install 'openai[async]'")
            raise

    # --- Provider 2: OpenAI-Compatible (Async) ---
    if PROVIDER == "openai_compat":
        try:
            import httpx
            url = os.getenv("OPENAI_COMPAT_BASE_URL") + "/v1/chat/completions"
            headers = {"Authorization": f"Bearer {os.getenv('OPENAI_COMPAT_API_KEY')}"}
            payload = {"model": MODEL, "messages": messages, **kwargs}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            
            response_data = response.json()
            
            # Track token usage if budget system is available
            if BUDGET_SYSTEM_AVAILABLE:
                tokens_used = response_data.get("usage", {}).get("total_tokens", 0)
                # Estimate input/output split (rough approximation)
                input_tokens = int(tokens_used * 0.7)
                output_tokens = tokens_used - input_tokens
                actual_cost = calculate_cost_usd(MODEL, input_tokens, output_tokens)
                
                record = UsageRecord(
                    scope="global",
                    model=MODEL,
                    tokens_input=input_tokens,
                    tokens_output=output_tokens,
                    cost_usd=actual_cost,
                    is_cache_hit=False,
                    provider=PROVIDER
                )
                budget_store.record_usage(record)

            return response_data["choices"][0]["message"]["content"]
        except ImportError:
            logger.error("httpx not available. Install with: pip install httpx")
            raise

    # --- Provider 3: Anthropic (Async) ---
    if PROVIDER == "anthropic":
        try:
            import anthropic
            client = anthropic.AsyncAnthropic()
            
            # Anthropic's async API
            response = await client.messages.create(model=MODEL, max_tokens=1024, messages=messages, **kwargs)
            
            # Track token usage if budget system is available
            if BUDGET_SYSTEM_AVAILABLE:
                input_tokens = response.usage.input_tokens if hasattr(response, 'usage') else 0
                output_tokens = response.usage.output_tokens if hasattr(response, 'usage') else 0
                actual_cost = calculate_cost_usd(MODEL, input_tokens, output_tokens)
                
                record = UsageRecord(
                    scope="global",
                    model=MODEL,
                    tokens_input=input_tokens,
                    tokens_output=output_tokens,
                    cost_usd=actual_cost,
                    is_cache_hit=False,
                    provider=PROVIDER
                )
                budget_store.record_usage(record)
            
            return response.content[0].text
        except ImportError:
            logger.error("Async Anthropic not available. Install with: pip install anthropic")
            raise

    # --- Error Handling ---
    raise ValueError(f"Async support not implemented for provider: {PROVIDER}")


def get_usage_summary(scope: str = "global"):
    """Get current token usage summary if budget system is available."""
    if BUDGET_SYSTEM_AVAILABLE:
        return budget_store.get_usage_summary(scope)
    return {"error": "Budget system not available"}


def reset_usage(scope: str = "global", period: str = "today"):
    """Reset usage for specified scope and period if budget system is available."""
    if BUDGET_SYSTEM_AVAILABLE:
        budget_store.reset_usage(scope, period)
        logger.info("Reset usage for scope %s (%s)", scope, period)
    else:
        logger.warning("Budget system not available")


def get_cache_stats():
    """Get cache statistics."""
    return cache_manager.get_stats()


def cleanup_cache():
    """Clean up expired cache entries."""
    return cache_manager.cleanup_expired()