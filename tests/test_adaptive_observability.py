import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock

from zerotoship.core.workflow_engine import WorkflowEngine
from zerotoship.core.learning_memory import LearningMemory
from zerotoship.core.crew_router import CrewRouter
from zerotoship.core.context_bus import ContextBus

class MockCrew:
    def __init__(self, status="success", delay=0.1, data=None):
        self.status = status
        self.delay = delay
        self.data = data or {}

    async def run(self, context):
        await asyncio.sleep(self.delay)
        return {
            "status": self.status,
            "message": "Crew run completed" if self.status == "success" else "Crew run failed",
            "data": self.data,
        }

@pytest.mark.asyncio
async def test_adaptive_observability_features():
    # 1. Setup Mocks
    project_data = {
        "id": "test_project_123",
        "idea": "A test project for observability",
        "workflow": "test_workflow",
        "state": "TASK_EXECUTION",
    }

    # Mock Crews and Router
    successful_crew = MockCrew(status="success", delay=0.1)
    crews = {"TASK_EXECUTION": successful_crew}
    context_bus = ContextBus()
    crew_router = CrewRouter(crews, context_bus)

    # Mock Learning Memory and Metrics
    memory = LearningMemory(store_path="data/test_memory_store.json")
    
    mock_crew_duration = MagicMock()
    mock_crew_failures = MagicMock()
    metrics = {
        "crew_duration_seconds": mock_crew_duration,
        "crew_failures_total": mock_crew_failures,
    }

    # 2. Instantiate WorkflowEngine
    engine = WorkflowEngine(
        project_data=project_data,
        crew_router=crew_router,
        metrics=metrics,
        memory=memory
    )
    # Since ContextBus is created inside WorkflowEngine, we need to get it from there
    # This is a flaw in the current design, but we work with it for the test.
    engine.context = context_bus


    # 3. Run a state transition
    project_data["state"] = "TASK_EXECUTION"
    await engine.handle_task_execution()

    # 4. Assertions
    # D1: Feedback Hooks
    feedback_history = await context_bus.get("TASK_EXECUTION_feedback_history")
    assert feedback_history is not None
    assert len(feedback_history) == 1
    feedback = feedback_history[0]
    assert feedback["status"] == "success"
    assert feedback["duration_seconds"] > 0.1

    # D4: Metrics
    mock_crew_duration.labels.assert_called_with(crew_name="TASK_EXECUTION")
    mock_crew_duration.labels().observe.assert_called_once()
    mock_crew_failures.labels().inc.assert_not_called()

    # D2: Memory Reinforcement (check at the end of a full run)
    # Simulate end of workflow to trigger memory add
    project_data["state"] = "COMPLETED"
    project_id = project_data.get("id")
    idea = project_data.get("idea")
    await memory.add(project_id, idea, "COMPLETED")
    
    # This is a simplified check. A real search would be better.
    assert len(memory._entries) == 1
    entry = memory._entries[0]
    assert entry["text"] == idea
    assert entry["success_count"] == 1
    assert entry["failure_count"] == 0
    assert entry["reliability_score"] == 1.0

    # D3: Dynamic Scaling (simplified check)
    # Run again to see if scaling logic is triggered
    await engine.handle_task_execution()
    # The check is based on logs, which is hard to assert here.
    # We can check the internal state of the router if we expose it,
    # but for now, this test focuses on what's easily observable.

    # Test failure case
    failing_crew = MockCrew(status="error", delay=0.1)
    crew_router.crews["VALIDATION"] = failing_crew
    project_data["state"] = "VALIDATION"
    await engine.handle_validation()
    
    mock_crew_failures.labels.assert_called_with(crew_name="VALIDATION")
    mock_crew_failures.labels().inc.assert_called() # Will be called 3 times due to retry
    assert mock_crew_failures.labels().inc.call_count == 3
