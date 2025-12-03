import asyncio, math
from datetime import datetime

class LearningMemory:
    def __init__(self):
        self._lock=asyncio.Lock();self._entries=[]
    async def add(self, project_id, text):
        async with self._lock:
            self._entries.append({"id":project_id,"text":text,"ts":datetime.utcnow().isoformat()})
    async def search(self, query, limit=3):
        async with self._lock:
            scored=[(e,self._score(query,e["text"])) for e in self._entries]
            return [x[0] for x in sorted(scored,key=lambda y:y[1],reverse=True)[:limit]]
    def _score(self,a,b):
        a,b=a.lower(),b.lower()
        return sum(1 for w in a.split() if w in b)/max(1,len(a.split()))