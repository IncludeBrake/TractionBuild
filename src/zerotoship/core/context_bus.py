import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional

class ContextBus:
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self.history: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()

    async def set(self, key: str, value: Any):
        async with self._lock:
            self._data[key] = value

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            return self._data.get(key)

    async def snapshot(self) -> Dict[str, Any]:
        async with self._lock:
            return self._data.copy()

    async def merge(self, data: Dict[str, Any]):
        async with self._lock:
            self._data.update(data)

    async def record(self, event_name: str, event_data: Dict[str, Any]):
        async with self._lock:
            self.history.append({
                "name": event_name,
                "data": event_data,
                "timestamp": datetime.utcnow().isoformat()
            })

    async def get_history(self) -> List[Dict[str, Any]]:
        async with self._lock:
            return self.history.copy()

    async def size(self) -> int:
        async with self._lock:
            return len(self._data)