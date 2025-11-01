import time
from src.tractionbuild.core.limits import RateLimiter, LatencyWindow

def test_rate_limiter_allows_then_blocks():
    rl = RateLimiter(capacity=2, interval_sec=10)
    assert rl.allow()
    assert rl.allow()
    assert not rl.allow()  # third should block without refill

def test_latency_p95():
    w = LatencyWindow(size=10)
    for ms in [10, 20, 30, 40, 50, 60, 70]:
        w.add(ms)
    p = w.p95()
    assert 60 <= p <= 70
