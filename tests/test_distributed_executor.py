"""
Tests for the DistributedExecutor.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock

from zerotoship.core.distributed_executor import DistributedExecutor

@pytest.mark.asyncio
async def test_distributed_executor_scheduling():
    mock_crew_router = AsyncMock()
    executor = DistributedExecutor(mock_crew_router, max_workers=1)
    
    await executor.start()
    
    test_context = {"key": "value"}
    test_project_data = {"id": "test_project"}
    
    await executor.schedule("TEST_STATE", test_context, test_project_data)
    
    await asyncio.sleep(0.1) # Give time for the worker to pick up the task
    
    mock_crew_router.execute.assert_called_once_with("TEST_STATE", test_context, test_project_data)
    
    await executor.stop()
