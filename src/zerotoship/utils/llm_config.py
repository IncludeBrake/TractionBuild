"""
LLM Configuration utilities for ZeroToShip.
Provides secure access to LLM API keys and configuration using Vault.
"""

import os
import logging
from typing import Dict, Any, Optional

# LLM availability flags - will be set when needed
OPENAI_AVAILABLE = None
ANTHROPIC_AVAILABLE = None
OLLAMA_AVAILABLE = None

from ..security.vault_client import VaultClient

logger = logging.getLogger(__name__)

class LLMConfig:
    """Secure LLM configuration using Vault for secret management."""
    
    def __init__(self):
        """Initialize LLM configuration with Vault client."""
        self.vault_client = VaultClient()
        self._cached_secrets = {}
    
    def get_openai_llm(self, model: str = "gpt-4o-mini", **kwargs) -> Optional[Any]:
        """Get OpenAI LLM with API key from Vault.
        
        Args:
            model: OpenAI model name
            **kwargs: Additional arguments for ChatOpenAI
            
        Returns:
            Configured ChatOpenAI instance or None if configuration fails
        """
        global OPENAI_AVAILABLE
        
        # Check availability dynamically
        if OPENAI_AVAILABLE is None:
            try:
                from langchain_openai import ChatOpenAI
                OPENAI_AVAILABLE = True
            except ImportError:
                OPENAI_AVAILABLE = False
                logger.error("OpenAI LLM not available - langchain_openai not installed")
                return None
        
        if not OPENAI_AVAILABLE:
            return None
            
        try:
            from langchain_openai import ChatOpenAI
            
            # Try to get secrets from Vault first
            secrets = self._get_cached_secrets("openai")
            if secrets and secrets.get("api_key"):
                api_key = secrets["api_key"]
                logger.info("Using OpenAI API key from Vault")
            else:
                # Fallback to environment variable
                api_key = os.getenv("OPENAI_API_KEY")
                if api_key:
                    logger.info("Using OpenAI API key from environment variable")
                else:
                    logger.error("No OpenAI API key found in Vault or environment")
                    return None
            
            return ChatOpenAI(
                model=model,
                api_key=api_key,
                **kwargs
            )
            
        except Exception as e:
            logger.error(f"Failed to configure OpenAI LLM: {e}")
            return None
    
    def get_anthropic_llm(self, model: str = "claude-3-sonnet-20240229", **kwargs) -> Optional[Any]:
        """Get Anthropic LLM with API key from Vault.
        
        Args:
            model: Anthropic model name
            **kwargs: Additional arguments for ChatAnthropic
            
        Returns:
            Configured ChatAnthropic instance or None if configuration fails
        """
        global ANTHROPIC_AVAILABLE
        
        # Check availability dynamically
        if ANTHROPIC_AVAILABLE is None:
            try:
                from langchain_anthropic import ChatAnthropic
                ANTHROPIC_AVAILABLE = True
            except ImportError:
                ANTHROPIC_AVAILABLE = False
                logger.error("Anthropic LLM not available - langchain_anthropic not installed")
                return None
        
        if not ANTHROPIC_AVAILABLE:
            return None
            
        try:
            from langchain_anthropic import ChatAnthropic
            
            # Try to get secrets from Vault first
            secrets = self._get_cached_secrets("anthropic")
            if secrets and secrets.get("api_key"):
                api_key = secrets["api_key"]
                logger.info("Using Anthropic API key from Vault")
            else:
                # Fallback to environment variable
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if api_key:
                    logger.info("Using Anthropic API key from environment variable")
                else:
                    logger.error("No Anthropic API key found in Vault or environment")
                    return None
            
            return ChatAnthropic(
                model=model,
                api_key=api_key,
                **kwargs
            )
            
        except Exception as e:
            logger.error(f"Failed to configure Anthropic LLM: {e}")
            return None
    
    def get_ollama_llm(self, model: str = "llama3.1:8b", **kwargs) -> Optional[Any]:
        """Get Ollama LLM with configuration from Vault.
        
        Args:
            model: Ollama model name
            **kwargs: Additional arguments for Ollama
            
        Returns:
            Configured Ollama instance or None if configuration fails
        """
        global OLLAMA_AVAILABLE
        
        # Check availability dynamically
        if OLLAMA_AVAILABLE is None:
            try:
                from langchain_community.llms import Ollama
                OLLAMA_AVAILABLE = True
            except ImportError:
                OLLAMA_AVAILABLE = False
                logger.error("Ollama LLM not available - langchain_community not installed")
                return None
        
        if not OLLAMA_AVAILABLE:
            return None
            
        try:
            from langchain_community.llms import Ollama
            
            # Try to get configuration from Vault first
            secrets = self._get_cached_secrets("ollama")
            base_url = None
            
            if secrets and secrets.get("base_url"):
                base_url = secrets["base_url"]
                logger.info("Using Ollama base URL from Vault")
            else:
                # Fallback to environment variable
                base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
                logger.info(f"Using Ollama base URL: {base_url}")
            
            return Ollama(
                model=model,
                base_url=base_url,
                **kwargs
            )
            
        except Exception as e:
            logger.error(f"Failed to configure Ollama LLM: {e}")
            return None
    
    def get_hybrid_llm(self, primary_provider: str = "openai", fallback_provider: str = "ollama", **kwargs) -> Optional[Any]:
        """Get a hybrid LLM configuration with primary and fallback providers.
        
        Args:
            primary_provider: Primary LLM provider ('openai', 'anthropic', 'ollama')
            fallback_provider: Fallback LLM provider
            **kwargs: Additional arguments for LLM configuration
            
        Returns:
            Configured LLM instance or None if configuration fails
        """
        try:
            # Try primary provider first
            if primary_provider == "openai":
                llm = self.get_openai_llm(**kwargs)
            elif primary_provider == "anthropic":
                llm = self.get_anthropic_llm(**kwargs)
            elif primary_provider == "ollama":
                llm = self.get_ollama_llm(**kwargs)
            else:
                logger.error(f"Unsupported primary provider: {primary_provider}")
                return None
            
            if llm:
                logger.info(f"Using {primary_provider} as primary LLM")
                return llm
            
            # Try fallback provider
            logger.warning(f"Primary provider {primary_provider} failed, trying fallback {fallback_provider}")
            if fallback_provider == "openai":
                llm = self.get_openai_llm(**kwargs)
            elif fallback_provider == "anthropic":
                llm = self.get_anthropic_llm(**kwargs)
            elif fallback_provider == "ollama":
                llm = self.get_ollama_llm(**kwargs)
            else:
                logger.error(f"Unsupported fallback provider: {fallback_provider}")
                return None
            
            if llm:
                logger.info(f"Using {fallback_provider} as fallback LLM")
                return llm
            
            logger.error("Both primary and fallback LLM providers failed")
            return None
            
        except Exception as e:
            logger.error(f"Failed to configure hybrid LLM: {e}")
            return None
    
    def _get_cached_secrets(self, provider: str) -> Optional[Dict[str, Any]]:
        """Get cached secrets for a provider, or fetch from Vault if not cached.
        
        Args:
            provider: LLM provider name
            
        Returns:
            Dictionary of secrets or None if not available
        """
        if provider not in self._cached_secrets:
            try:
                secrets = self.vault_client.read_llm_secrets(provider)
                self._cached_secrets[provider] = secrets
            except Exception as e:
                logger.warning(f"Failed to read {provider} secrets from Vault: {e}")
                self._cached_secrets[provider] = None
        
        return self._cached_secrets[provider]
    
    def test_llm_connection(self, provider: str = "openai") -> Dict[str, Any]:
        """Test LLM connection and configuration.
        
        Args:
            provider: LLM provider to test
            
        Returns:
            Dictionary with test results
        """
        result = {
            "provider": provider,
            "vault_available": self.vault_client.enabled,
            "vault_authenticated": self.vault_client.authenticated,
            "secrets_available": False,
            "llm_configured": False,
            "connection_successful": False,
            "error": None
        }
        
        try:
            # Test secrets availability
            secrets = self._get_cached_secrets(provider)
            result["secrets_available"] = secrets is not None
            
            # Test LLM configuration
            if provider == "openai":
                llm = self.get_openai_llm()
            elif provider == "anthropic":
                llm = self.get_anthropic_llm()
            elif provider == "ollama":
                llm = self.get_ollama_llm()
            else:
                result["error"] = f"Unsupported provider: {provider}"
                return result
            
            result["llm_configured"] = llm is not None
            
            # Test connection with a simple query
            if llm:
                try:
                    response = llm.invoke("Hello, this is a test message.")
                    result["connection_successful"] = True
                    result["response_preview"] = str(response)[:100] + "..." if len(str(response)) > 100 else str(response)
                except Exception as e:
                    result["error"] = f"Connection test failed: {e}"
            
        except Exception as e:
            result["error"] = str(e)
        
        return result


# Global LLM configuration instance
llm_config = LLMConfig()
