# llm.py
import os
import requests
import json
import hashlib
from functools import wraps

# --- Reading configuration from environment variables ---
# This determines which provider's logic to use below. Defaults to "openai".
PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()

# This sets the specific model name for the chosen provider.
MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

# A simple in-memory cache
_cache = {}

def cache_result(func):
    @wraps(func)
    def wrapper(messages, **kwargs):
        # Create a unique key based on the messages and model
        message_str = json.dumps(messages, sort_keys=True)
        key_str = f"{MODEL}:{message_str}"
        key = hashlib.md5(key_str.encode()).hexdigest()

        if key in _cache:
            print("--- Returning response from cache ---")
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
    print(f"--- Routing to LLM Provider: {PROVIDER}, Model: {MODEL} ---")

    # --- Provider 1: OpenAI ---
    if PROVIDER == "openai":
        # You need to install the openai library: pip install openai
        from openai import OpenAI
        client = OpenAI() # The client automatically looks for the OPENAI_API_KEY env var
        response = client.chat.completions.create(model=MODEL, messages=messages, **kwargs)
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

        return response.json()["choices"][0]["message"]["content"]

    # --- Provider 3: Anthropic ---
    if PROVIDER == "anthropic":
        # You need to install the anthropic library: pip install anthropic
        import anthropic
        client = anthropic.Anthropic() # The client automatically looks for ANTHROPIC_API_KEY env var

        # Anthropic's API has a slightly different structure
        response = client.messages.create(model=MODEL, max_tokens=1024, messages=messages, **kwargs)
        return response.content[0].text

    # --- Error Handling ---
    raise ValueError(f"Unknown or unsupported LLM_PROVIDER: {PROVIDER}")