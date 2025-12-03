"""
ContextBus - Shared async key-value store for crews.
Provides thread-safe access to shared workflow context and event history.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class ContextBus:
    """
    Shared async key-value store for workflow context.

    Features:
    - Thread-safe async operations
    - Key-value storage
    - Bulk merge operations
    - Event history tracking
    - Snapshot capability
    """

    def __init__(self):
        """Initialize the ContextBus."""
        self._lock = asyncio.Lock()
        self._data: Dict[str, Any] = {}
        self.history: List[Dict[str, Any]] = []
        logger.info("ContextBus initialized")

    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the context.

        Args:
            key: The key to retrieve
            default: Default value if key doesn't exist

        Returns:
            The value associated with the key, or default if not found
        """
        async with self._lock:
            value = self._data.get(key, default)
            logger.debug(f"ContextBus.get: {key} = {value}")
            return value

    async def set(self, key: str, value: Any) -> None:
        """
        Set a value in the context.

        Args:
            key: The key to set
            value: The value to store
        """
        async with self._lock:
            self._data[key] = value
            logger.debug(f"ContextBus.set: {key} = {value}")

    async def merge(self, updates: Optional[Dict[str, Any]]) -> None:
        """
        Merge multiple key-value pairs into the context.

        Args:
            updates: Dictionary of key-value pairs to merge
        """
        if not updates:
            return

        async with self._lock:
            self._data.update(updates)
            logger.debug(f"ContextBus.merge: {len(updates)} keys updated")

    async def snapshot(self) -> Dict[str, Any]:
        """
        Get a snapshot of the current context.

        Returns:
            A copy of the current context dictionary
        """
        async with self._lock:
            snapshot = dict(self._data)
            logger.debug(f"ContextBus.snapshot: {len(snapshot)} keys")
            return snapshot

    async def record(self, event: str, payload: Any = None) -> None:
        """
        Record an event in the history.

        Args:
            event: Event name/description
            payload: Optional event payload
        """
        async with self._lock:
            event_record = {
                "event": event,
                "payload": payload,
                "timestamp": datetime.now().isoformat()
            }
            self.history.append(event_record)
            logger.info(f"ContextBus.record: {event}")

    async def get_history(self) -> List[Dict[str, Any]]:
        """
        Get the complete event history.

        Returns:
            List of all recorded events
        """
        async with self._lock:
            return list(self.history)

    async def clear(self) -> None:
        """Clear all context data (useful for testing)."""
        async with self._lock:
            self._data.clear()
            logger.info("ContextBus cleared")

    async def size(self) -> int:
        """Get the number of keys in the context."""
        async with self._lock:
            return len(self._data)
