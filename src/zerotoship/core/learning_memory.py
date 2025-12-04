import asyncio, math
import json
import os
from datetime import datetime

class LearningMemory:
    def __init__(self, store_path: str = "data/memory_store.json"):
        self._lock=asyncio.Lock()
        self._entries=[]
        self.store_path = store_path

    async def add(self, project_id, text=None, status: str = "COMPLETED"):
        async with self._lock:
            if isinstance(project_id, dict):
                record = project_id
                project_id = record.get("id") or record.get("project_id") or "unknown"
                text = record.get("idea") or record.get("text") or ""
                status = record.get("status") or record.get("state") or status

            # Find existing entry by text (idea)
            existing_entry = next((e for e in self._entries if e["text"] == text), None)

            if existing_entry:
                # Update existing entry
                if status == "COMPLETED":
                    existing_entry["success_count"] += 1
                else:
                    existing_entry["failure_count"] += 1
                
                # Update timestamp and score
                existing_entry["ts"] = datetime.utcnow().isoformat()
                existing_entry["reliability_score"] = self._calculate_reliability(
                    existing_entry["success_count"], existing_entry["failure_count"]
                )
            else:
                # Create new entry
                success = 1 if status == "COMPLETED" else 0
                failure = 1 if status != "COMPLETED" else 0
                new_entry = {
                    "id": project_id,
                    "text": text or "",
                    "ts": datetime.utcnow().isoformat(),
                    "success_count": success,
                    "failure_count": failure,
                    "reliability_score": self._calculate_reliability(success, failure),
                }
                self._entries.append(new_entry)

    async def search(self, query, limit=3):
        async with self._lock:
            scored=[(e,self._score(query,e["text"])) for e in self._entries]
            return [x[0] for x in sorted(scored,key=lambda y:y[1],reverse=True)[:limit]]

    async def persist(self):
        async with self._lock:
            if not os.path.exists(os.path.dirname(self.store_path)):
                os.makedirs(os.path.dirname(self.store_path))
            with open(self.store_path, 'w') as f:
                json.dump(self._entries, f, indent=2)

    async def load(self):
        async with self._lock:
            if os.path.exists(self.store_path):
                with open(self.store_path, 'r') as f:
                    self._entries = json.load(f)

    def _score(self,a,b):
        a,b=a.lower(),b.lower()
        return sum(1 for w in a.split() if w in b)/max(1,len(a.split()))

    def _calculate_reliability(self, success, failure):
        total = success + failure
        if total == 0:
            return 0.5  # Neutral score for new entries
        return success / total

    def query(self, query: str):
        """Return the most relevant learning memory entry matching the query."""
        if not self._entries:
            return {}
        scored = [(entry, self._score(query, entry.get("text", ""))) for entry in self._entries]
        best, score = max(scored, key=lambda item: item[1])
        return best if score > 0 else {}

    def reliability_score(self, entity_id: str) -> float:
        entry = next((e for e in self._entries if e.get("id") == entity_id), None)
        if not entry:
            return 0.5
        return entry.get("reliability_score", 0.5)
