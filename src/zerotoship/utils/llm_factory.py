import os
import logging
from typing import Optional, Any
from ..security.vault_client import VaultClient

logger = logging.getLogger(__name__)

# LLM availability flags - will be set when needed
OPENAI_AVAILABLE = None
ANTHROPIC_AVAILABLE = None
OLLAMA_AVAILABLE = None

def get_llm() -> Any:
    """
    An LLM Factory that reads environment variables and returns the
    appropriate, initialized LLM client (e.g., OpenAI, Anthropic, Ollama).
    
    Returns:
        An initialized LangChain LLM client
        
    Raises:
        Exception: If no LLM client can be initialized
    """
    # Determine which LLM provider to use from the environment variable.
    # Defaults to 'openai' if not set.
    llm_provider = os.getenv("LLM_PROVIDER", "openai").lower()
    
    logger.info(f"LLM Factory: Initializing LLM for provider: '{llm_provider}'")
    
    # Initialize the Vault client to fetch API keys securely
    vault = VaultClient()

    if llm_provider == "anthropic":
        try:
            global ANTHROPIC_AVAILABLE
            if ANTHROPIC_AVAILABLE is None:
                try:
                    from langchain_anthropic import ChatAnthropic
                    ANTHROPIC_AVAILABLE = True
                except ImportError:
                    ANTHROPIC_AVAILABLE = False
                    logger.error("Anthropic LLM not available - langchain_anthropic not installed")
            
            if not ANTHROPIC_AVAILABLE:
                raise ImportError("Anthropic LLM not available")
            
            from langchain_anthropic import ChatAnthropic
            anthropic_secrets = vault.get_secret('zerotoship/llm/anthropic')
            api_key = anthropic_secrets.get('api_key') if anthropic_secrets else os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("Anthropic API key not found in Vault or environment.")
            
            # Return the LangChain client for Anthropic (Claude)
            return ChatAnthropic(model='claude-3-sonnet-20240229', api_key=api_key)
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}. Falling back to OpenAI.")
            # Fallback to OpenAI on failure
            pass

    if llm_provider == "ollama":
        try:
            global OLLAMA_AVAILABLE
            if OLLAMA_AVAILABLE is None:
                try:
                    from langchain_community.chat_models import ChatOllama
                    OLLAMA_AVAILABLE = True
                except ImportError:
                    OLLAMA_AVAILABLE = False
                    logger.error("Ollama LLM not available - langchain_community not installed")
            
            if not OLLAMA_AVAILABLE:
                raise ImportError("Ollama LLM not available")
            
            from langchain_community.chat_models import ChatOllama
            # Return the LangChain client for a local Ollama model
            return ChatOllama(model=os.getenv("OLLAMA_MODEL", "llama3.1:8b"))
        except Exception as e:
            logger.error(f"Failed to initialize Ollama client: {e}. Falling back to OpenAI.")
            pass
            
    # Default to OpenAI
    try:
        global OPENAI_AVAILABLE
        if OPENAI_AVAILABLE is None:
            try:
                from langchain_openai import ChatOpenAI
                OPENAI_AVAILABLE = True
            except ImportError:
                OPENAI_AVAILABLE = False
                logger.error("OpenAI LLM not available - langchain_openai not installed")
        
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI LLM not available")
        
        from langchain_openai import ChatOpenAI
        openai_secrets = vault.get_secret('zerotoship/llm/openai')
        api_key = openai_secrets.get('api_key') if openai_secrets else os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found in Vault or environment.")
        
        # Return the LangChain client for OpenAI (GPT)
        return ChatOpenAI(model='gpt-4o-mini', api_key=api_key)
    except Exception as e:
        logger.error(f"FATAL: Could not initialize any LLM client. OpenAI fallback failed: {e}")
        # If even the default fails, raise the exception to halt the application.
        raise

def get_llm_with_fallback(primary_provider: str = None, fallback_provider: str = "openai") -> Any:
    """
    Get LLM with explicit primary and fallback providers.
    
    Args:
        primary_provider: Primary LLM provider to try first
        fallback_provider: Fallback provider if primary fails
        
    Returns:
        An initialized LangChain LLM client
    """
    if primary_provider:
        # Try primary provider first
        try:
            original_provider = os.getenv("LLM_PROVIDER")
            os.environ["LLM_PROVIDER"] = primary_provider
            llm = get_llm()
            logger.info(f"Successfully initialized {primary_provider} LLM")
            return llm
        except Exception as e:
            logger.warning(f"Primary provider {primary_provider} failed: {e}")
            # Restore original provider setting
            if original_provider:
                os.environ["LLM_PROVIDER"] = original_provider
            else:
                os.environ.pop("LLM_PROVIDER", None)
    
    # Try fallback provider
    try:
        original_provider = os.getenv("LLM_PROVIDER")
        os.environ["LLM_PROVIDER"] = fallback_provider
        llm = get_llm()
        logger.info(f"Successfully initialized {fallback_provider} LLM as fallback")
        return llm
    except Exception as e:
        logger.error(f"Fallback provider {fallback_provider} also failed: {e}")
        # Restore original provider setting
        if original_provider:
            os.environ["LLM_PROVIDER"] = original_provider
        else:
            os.environ.pop("LLM_PROVIDER", None)
        raise

def test_llm_connection(provider: str = None) -> dict:
    """
    Test LLM connection for a specific provider.
    
    Args:
        provider: Provider to test (if None, uses current LLM_PROVIDER)
        
    Returns:
        Dictionary with test results
    """
    result = {
        "provider": provider or os.getenv("LLM_PROVIDER", "openai"),
        "success": False,
        "error": None,
        "model_info": None
    }
    
    try:
        if provider:
            original_provider = os.getenv("LLM_PROVIDER")
            os.environ["LLM_PROVIDER"] = provider
        
        llm = get_llm()
        
        # Test with a simple query
        response = llm.invoke("Hello, this is a test message.")
        
        result["success"] = True
        result["model_info"] = {
            "type": type(llm).__name__,
            "model": getattr(llm, 'model', getattr(llm, 'model_name', 'unknown')),
            "response_preview": str(response)[:100] + "..." if len(str(response)) > 100 else str(response)
        }
        
    except Exception as e:
        result["error"] = str(e)
    finally:
        # Restore original provider setting
        if provider and 'original_provider' in locals():
            if original_provider:
                os.environ["LLM_PROVIDER"] = original_provider
            else:
                os.environ.pop("LLM_PROVIDER", None)
    
    return result
