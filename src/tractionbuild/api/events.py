import asyncio
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class EventBus:
    def __init__(self):
        self.queues: Dict[str, asyncio.Queue] = {}
    
    def queue(self, project_id: str) -> asyncio.Queue:
        if project_id not in self.queues:
            self.queues[project_id] = asyncio.Queue()
        return self.queues[project_id]
    
    async def emit(self, project_id: str, event: dict):
        if project_id in self.queues:
            await self.queues[project_id].put(event)
            logger.info(f"Event emitted for project {project_id}: {event}")

bus = EventBus()
