class ContextBus:
    async def set(self, k, v): pass
    async def snapshot(self): return {}
    async def merge(self, d): pass
    async def get_history(self): return []
    async def record(self, e, r): pass
    async def size(self): return 0