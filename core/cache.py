"""
Versioned cache system with TTL and message normalization.
Provides robust caching for LLM operations with schema versioning.
"""

import json
import hashlib
import time
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# Cache schema version - increment when cache format changes
CACHE_SCHEMA_VERSION = "1.0"

@dataclass
class CacheConfig:
    """Configuration for cache behavior."""
    ttl_seconds: int = 3600  # 1 hour default
    max_size: int = 1000  # Maximum number of cached items
    enable_pii_redaction: bool = True

# Model-specific TTL configurations
MODEL_TTL_CONFIGS = {
    "gpt-4o-mini": 1800,  # 30 minutes for fast models
    "gpt-4o": 3600,       # 1 hour for standard models
    "gpt-4": 7200,        # 2 hours for expensive models
    "claude-3-sonnet": 3600,
    "claude-3-haiku": 1800,
    "llama3.1:8b": 600,   # 10 minutes for local models
}

def normalize_messages(messages: List[Dict[str, Any]], enable_pii_redaction: bool = True) -> str:
    """
    Normalize messages for consistent cache key generation.
    
    Args:
        messages: List of message dictionaries
        enable_pii_redaction: Whether to redact PII for cache keys
        
    Returns:
        Normalized JSON string
    """
    if not messages:
        return "[]"
    
    # Deep copy to avoid modifying original
    normalized = []
    for msg in messages:
        normalized_msg = {
            "role": msg.get("role", "").lower().strip(),
            "content": msg.get("content", "").strip()
        }
        
        if enable_pii_redaction:
            normalized_msg["content"] = redact_pii(normalized_msg["content"])
        
        normalized.append(normalized_msg)
    
    # Sort by role and content for consistent ordering
    normalized.sort(key=lambda x: (x["role"], x["content"]))
    
    return json.dumps(normalized, sort_keys=True, separators=(',', ':'))

def redact_pii(text: str) -> str:
    """
    Redact personally identifiable information from text.
    
    Args:
        text: Input text
        
    Returns:
        Text with PII redacted
    """
    if not text:
        return text
    
    # Email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '<EMAIL>', text)
    
    # 16+ hex characters (likely hashes, IDs)
    text = re.sub(r'\b[A-Fa-f0-9]{16,}\b', '<HEX>', text)
    
    # 6+ digit numbers (likely phone numbers, IDs)
    text = re.sub(r'\b\d{6,}\b', '<NUM>', text)
    
    # Credit card numbers (basic pattern)
    text = re.sub(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b', '<CC>', text)
    
    # Social security numbers (US)
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '<SSN>', text)
    
    return text

def generate_cache_key(messages: List[Dict[str, Any]], model: str, **kwargs) -> str:
    """
    Generate a versioned cache key for messages and model.
    
    Args:
        messages: List of message dictionaries
        model: Model name
        **kwargs: Additional parameters to include in key
        
    Returns:
        Cache key string
    """
    # Normalize messages
    normalized_messages = normalize_messages(messages)
    
    # Create key components
    key_components = {
        "schema_version": CACHE_SCHEMA_VERSION,
        "model": model.lower().strip(),
        "messages": normalized_messages
    }
    
    # Add relevant kwargs (exclude non-deterministic ones)
    relevant_kwargs = {}
    for key, value in kwargs.items():
        if key in ["temperature", "max_tokens", "top_p", "frequency_penalty", "presence_penalty"]:
            # Round floats to avoid precision issues
            if isinstance(value, float):
                relevant_kwargs[key] = round(value, 3)
            else:
                relevant_kwargs[key] = value
    
    if relevant_kwargs:
        key_components["params"] = relevant_kwargs
    
    # Generate hash
    key_str = json.dumps(key_components, sort_keys=True, separators=(',', ':'))
    return hashlib.md5(key_str.encode()).hexdigest()

def get_cache_ttl(model: str) -> int:
    """
    Get TTL for a specific model.
    
    Args:
        model: Model name
        
    Returns:
        TTL in seconds
    """
    return MODEL_TTL_CONFIGS.get(model.lower(), 3600)  # Default 1 hour

class CacheManager:
    """Manages cache operations with TTL and size limits."""
    
    def __init__(self, config: Optional[CacheConfig] = None):
        """Initialize cache manager."""
        self.config = config or CacheConfig()
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_times: Dict[str, float] = {}
    
    def get(self, key: str) -> Optional[str]:
        """
        Get value from cache if not expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            return None
        
        cache_entry = self._cache[key]
        current_time = time.time()
        
        # Check TTL
        if current_time - cache_entry["created_at"] > cache_entry["ttl"]:
            self._remove(key)
            return None
        
        # Update access time for LRU
        self._access_times[key] = current_time
        
        logger.debug("Cache hit for key: %s", key[:8] + "...")
        return cache_entry["value"]
    
    def set(self, key: str, value: str, model: str) -> None:
        """
        Set value in cache with model-specific TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            model: Model name for TTL calculation
        """
        current_time = time.time()
        ttl = get_cache_ttl(model)
        
        # Check size limit and evict if necessary
        if len(self._cache) >= self.config.max_size:
            self._evict_lru()
        
        self._cache[key] = {
            "value": value,
            "created_at": current_time,
            "ttl": ttl,
            "model": model
        }
        self._access_times[key] = current_time
        
        logger.debug("Cached value for key: %s (TTL: %ds)", key[:8] + "...", ttl)
    
    def _remove(self, key: str) -> None:
        """Remove key from cache."""
        self._cache.pop(key, None)
        self._access_times.pop(key, None)
    
    def _evict_lru(self) -> None:
        """Evict least recently used item."""
        if not self._access_times:
            return
        
        # Find LRU key
        lru_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
        self._remove(lru_key)
        logger.debug("Evicted LRU cache entry: %s", lru_key[:8] + "...")
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._access_times.clear()
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        current_time = time.time()
        active_entries = 0
        expired_entries = 0
        
        for entry in self._cache.values():
            if current_time - entry["created_at"] <= entry["ttl"]:
                active_entries += 1
            else:
                expired_entries += 1
        
        return {
            "total_entries": len(self._cache),
            "active_entries": active_entries,
            "expired_entries": expired_entries,
            "max_size": self.config.max_size,
            "schema_version": CACHE_SCHEMA_VERSION
        }
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self._cache.items():
            if current_time - entry["created_at"] > entry["ttl"]:
                expired_keys.append(key)
        
        for key in expired_keys:
            self._remove(key)
        
        if expired_keys:
            logger.info("Cleaned up %d expired cache entries", len(expired_keys))
        
        return len(expired_keys)

# Global cache manager instance
cache_manager = CacheManager()
