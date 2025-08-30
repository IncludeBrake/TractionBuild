import asyncio
from collections import defaultdict
from typing import Dict

class EventBus:
    def __init__(self):
        self.queues: Dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)

    def queue(self, project_id: str) -> asyncio.Queue:
        return self.queues[project_id]

    async def emit(self, project_id: str, event: dict) -> None:
        await self.queues[project_id].put(event)

bus = EventBus()  # import this, never re-instantiate

