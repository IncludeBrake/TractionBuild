"""
Tests for the TemporalMemory.
"""
import pytest
from datetime import datetime, timedelta

from zerotoship.core.temporal_memory import TemporalMemory

def test_temporal_memory_replay():
    memory = TemporalMemory()
    
    now = datetime.utcnow()
    
    memory.record("event1", {"data": "a"})
    memory.record("event2", {"data": "b"})
    
    replayed = memory.replay(now + timedelta(seconds=1))
    assert len(replayed) == 2
    
    past_time = now - timedelta(seconds=1)
    replayed_past = memory.replay(past_time)
    assert len(replayed_past) == 0
