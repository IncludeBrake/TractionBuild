"""
Tests for ContextBus - Shared async key-value store.
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.zerotoship.core.context_bus import ContextBus


@pytest.mark.asyncio
async def test_context_bus_get_set():
    """Test basic get/set operations."""
    ctx = ContextBus()

    # Set a value
    await ctx.set("foo", "bar")

    # Get the value
    value = await ctx.get("foo")
    assert value == "bar"

    # Get non-existent key with default
    value = await ctx.get("nonexistent", "default_value")
    assert value == "default_value"


@pytest.mark.asyncio
async def test_context_bus_merge():
    """Test bulk merge operations."""
    ctx = ContextBus()

    # Set initial value
    await ctx.set("foo", "bar")

    # Merge additional values
    await ctx.merge({"x": 1, "y": 2, "z": 3})

    # Verify all values
    snap = await ctx.snapshot()
    assert snap["foo"] == "bar"
    assert snap["x"] == 1
    assert snap["y"] == 2
    assert snap["z"] == 3


@pytest.mark.asyncio
async def test_context_bus_snapshot():
    """Test snapshot returns a copy."""
    ctx = ContextBus()

    await ctx.set("key1", "value1")
    await ctx.set("key2", "value2")

    # Get snapshot
    snap1 = await ctx.snapshot()
    assert len(snap1) == 2

    # Modify snapshot (should not affect context)
    snap1["key3"] = "value3"

    # Get new snapshot
    snap2 = await ctx.snapshot()
    assert len(snap2) == 2  # Should still be 2
    assert "key3" not in snap2


@pytest.mark.asyncio
async def test_context_bus_record_history():
    """Test event recording."""
    ctx = ContextBus()

    # Record events
    await ctx.record("event1", {"data": "payload1"})
    await ctx.record("event2", {"data": "payload2"})
    await ctx.record("event3")

    # Get history
    history = await ctx.get_history()
    assert len(history) == 3
    assert history[0]["event"] == "event1"
    assert history[1]["event"] == "event2"
    assert history[2]["event"] == "event3"
    assert "timestamp" in history[0]


@pytest.mark.asyncio
async def test_context_bus_clear():
    """Test clearing context."""
    ctx = ContextBus()

    await ctx.set("foo", "bar")
    await ctx.set("baz", "qux")

    size = await ctx.size()
    assert size == 2

    await ctx.clear()

    size = await ctx.size()
    assert size == 0

    snap = await ctx.snapshot()
    assert len(snap) == 0


@pytest.mark.asyncio
async def test_context_bus_size():
    """Test size tracking."""
    ctx = ContextBus()

    size = await ctx.size()
    assert size == 0

    await ctx.set("a", 1)
    size = await ctx.size()
    assert size == 1

    await ctx.merge({"b": 2, "c": 3})
    size = await ctx.size()
    assert size == 3


@pytest.mark.asyncio
async def test_context_bus_concurrent_access():
    """Test thread-safe concurrent access."""
    ctx = ContextBus()

    # Define concurrent operations
    async def writer(key, value):
        await ctx.set(key, value)

    async def reader(key):
        return await ctx.get(key, None)

    # Execute multiple writes concurrently
    await asyncio.gather(
        writer("key1", "value1"),
        writer("key2", "value2"),
        writer("key3", "value3"),
        writer("key4", "value4"),
    )

    # Verify all writes succeeded
    snap = await ctx.snapshot()
    assert len(snap) == 4
    assert snap["key1"] == "value1"
    assert snap["key4"] == "value4"


@pytest.mark.asyncio
async def test_context_bus_merge_none():
    """Test that merging None doesn't cause errors."""
    ctx = ContextBus()

    await ctx.set("foo", "bar")
    await ctx.merge(None)

    snap = await ctx.snapshot()
    assert snap["foo"] == "bar"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
