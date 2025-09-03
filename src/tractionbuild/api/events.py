import asyncio
from collections import defaultdict
from typing import Dict

# Simple event bus placeholder
class EventBus:
    def __init__(self):
        self.listeners = {}
    
    def emit(self, event, data=None):
        pass
    
    def on(self, event, callback):
        pass

bus = EventBus()  # import this, never re-instantiate
