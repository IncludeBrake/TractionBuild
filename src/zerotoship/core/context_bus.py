import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional


class ContextBus:
    def __init__(self, external_data_sources: List[str] = None):
        self._data: Dict[str, Any] = {}
        self.history: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()
        self.external_data_sources = external_data_sources or []

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

    async def fetch_and_merge_external_data(self):
        if not self.external_data_sources:
            return

        urls = " ".join(self.external_data_sources)
        prompt = f"Please summarize the content of the following URLs: {urls}"
        
        try:
            # Note: The web_fetch tool is a placeholder for a real implementation.
            # In a real scenario, this would be a robust service call.
            fetched_data = await web_fetch(prompt=prompt)
            
            # Assuming fetched_data is a dictionary where keys are URLs and values are summaries.
            # In a real implementation, you would parse the output of the web_fetch tool.
            if fetched_data:
                await self.merge({"external_data": fetched_data})
        except Exception as e:
            # In a real scenario, you would handle this error more gracefully.
            print(f"Error fetching external data: {e}")