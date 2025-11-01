from __future__ import annotations
import time
from collections import deque
from typing import Deque

class RateLimiter:
    """Simple token bucket: N calls per interval seconds."""
    def __init__(self, capacity: int, interval_sec: float):
        self.capacity = capacity
        self.interval = interval_sec
        self.tokens = capacity
        self.ts = time.time()

    def allow(self) -> bool:
        now = time.time()
        elapsed = now - self.ts
        refill = int(elapsed // self.interval)
        if refill > 0:
            self.tokens = min(self.capacity, self.tokens + refill)
            self.ts += refill * self.interval
        if self.tokens > 0:
            self.tokens -= 1
            return True
        return False

class LatencyWindow:
    """Sliding window p95 over last N samples."""
    def __init__(self, size: int = 200):
        self.size = size
        self.samples: Deque[float] = deque(maxlen=size)

    def add(self, ms: float) -> None:
        self.samples.append(ms)

    def p95(self) -> float:
        if not self.samples:
            return 0.0
        arr = sorted(self.samples)
        k = int(round(0.95 * (len(arr)-1)))
        return arr[k]
