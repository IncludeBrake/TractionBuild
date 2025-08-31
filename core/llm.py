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

# A simple in-memory cache
_cache = {}

# Import token budget manager
try:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
    from zerotoship.utils.token_budget import token_budget
    TOKEN_BUDGET_AVAILABLE = True
except ImportError:
    TOKEN_BUDGET_AVAILABLE = False
    print("--- Token budget tracking not available ---")

# Enhanced logging setup
import logging
logger = logging.getLogger(__name__)

def cache_result(func):
    @wraps(func)
    def wrapper(messages, **kwargs):
        # Create a unique key based on the messages and model
        message_str = json.dumps(messages, sort_keys=True)
        key_str = f"{MODEL}:{message_str}"
        key = hashlib.md5(key_str.encode()).hexdigest()

        if key in _cache:
            logger.info("Returning response from cache for key: %s", key[:8] + "...")
            # Record cache hit if budget tracking is available
            if TOKEN_BUDGET_AVAILABLE:
                token_budget.record_usage(0, is_cache_hit=True, model=MODEL)
            return _cache[key]
        
        # If not in cache, call the original function and store the result
        result = func(messages, **kwargs)
        _cache[key] = result
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
        response = client.chat.completions.create(model=MODEL, messages=messages, **kwargs)
        
        # Track token usage if budget tracking is available
        if TOKEN_BUDGET_AVAILABLE:
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
            token_budget.record_usage(tokens_used, is_cache_hit=False, model=MODEL)
        
        return response.choices[0].message.content

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
        
        # Track token usage if budget tracking is available
        if TOKEN_BUDGET_AVAILABLE:
            tokens_used = response_data.get("usage", {}).get("total_tokens", 0)
            token_budget.record_usage(tokens_used, is_cache_hit=False, model=MODEL)

        return response_data["choices"][0]["message"]["content"]

    # --- Provider 3: Anthropic ---
    if PROVIDER == "anthropic":
        # You need to install the anthropic library: pip install anthropic
        import anthropic
        client = anthropic.Anthropic() # The client automatically looks for ANTHROPIC_API_KEY env var

        # Anthropic's API has a slightly different structure
        response = client.messages.create(model=MODEL, max_tokens=1024, messages=messages, **kwargs)
        
        # Track token usage if budget tracking is available
        if TOKEN_BUDGET_AVAILABLE:
            tokens_used = response.usage.input_tokens + response.usage.output_tokens if hasattr(response, 'usage') else 0
            token_budget.record_usage(tokens_used, is_cache_hit=False, model=MODEL)
        
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
            
            # Track token usage if budget tracking is available
            if TOKEN_BUDGET_AVAILABLE:
                tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
                token_budget.record_usage(tokens_used, is_cache_hit=False, model=MODEL)
            
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
            
            # Track token usage if budget tracking is available
            if TOKEN_BUDGET_AVAILABLE:
                tokens_used = response_data.get("usage", {}).get("total_tokens", 0)
                token_budget.record_usage(tokens_used, is_cache_hit=False, model=MODEL)

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
            
            # Track token usage if budget tracking is available
            if TOKEN_BUDGET_AVAILABLE:
                tokens_used = response.usage.input_tokens + response.usage.output_tokens if hasattr(response, 'usage') else 0
                token_budget.record_usage(tokens_used, is_cache_hit=False, model=MODEL)
            
            return response.content[0].text
        except ImportError:
            logger.error("Async Anthropic not available. Install with: pip install anthropic")
            raise

    # --- Error Handling ---
    raise ValueError(f"Async support not implemented for provider: {PROVIDER}")


def get_usage_summary():
    """Get current token usage summary if budget tracking is available."""
    if TOKEN_BUDGET_AVAILABLE:
        return token_budget.get_usage_summary()
    return {"error": "Token budget tracking not available"}


def reset_usage(period: str = "today"):
    """Reset usage for specified period if budget tracking is available."""
    if TOKEN_BUDGET_AVAILABLE:
        token_budget.reset_usage(period)
        logger.info("Reset usage for period: %s", period)
    else:
        logger.warning("Token budget tracking not available")