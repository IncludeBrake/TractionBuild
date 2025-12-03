"""
Temporal Memory for replaying workflow states.
"""
from datetime import datetime

class TemporalMemory:
    def __init__(self):
        self.events = []

    def record(self, event_name, event_data):
        self.events.append({
            "name": event_name,
            "data": event_data,
            "timestamp": datetime.utcnow().isoformat(),
        })

    def replay(self, to_timestamp: datetime):
        # This is a simplified replay. A real implementation would be more complex.
        replayed_events = [e for e in self.events if datetime.fromisoformat(e["timestamp"]) <= to_timestamp]
        return replayed_events
