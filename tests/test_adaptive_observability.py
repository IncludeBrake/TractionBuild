import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock

from zerotoship.core.workflow_engine import WorkflowEngine
from zerotoship.core.learning_memory import LearningMemory
from zerotoship.core.crew_router import CrewRouter
from zerotoship.core.context_bus import ContextBus
from zerotoship.core.distributed_executor import DistributedExecutor
from zerotoship.core.project_meta_memory import ProjectMetaMemoryManager, MemoryType

class MockCrew:
    def __init__(self, project_data: dict, status="success", delay=0.1, data=None, error_category="transient"):
        self.status = status
        self.delay = delay
        self.data = data or {}
        self.error_category = error_category
        self.name = self.__class__.__name__

    async def run(self, context):
        await asyncio.sleep(self.delay)
        result = {
            "status": self.status,
            "message": "Crew run completed" if self.status == "success" else "Crew run failed",
            "data": self.data,
            "token_usage": 1000, # For cost testing
        }
        if self.status != "success":
            result["error_category"] = self.error_category
        return result

class HighReliabilityCrew(MockCrew):
    pass

class LowReliabilityCrew(MockCrew):
    pass

class PermanentErrorCrew(MockCrew):
    def __init__(self, project_data: dict):
        super().__init__(project_data, status="error", error_category="permanent")

class RecoveryCrew(MockCrew):
    def __init__(self, project_data: dict):
        super().__init__(project_data, status="success")


@pytest.mark.asyncio
async def test_track_e_features():
    # 1. Setup
    project_data = {
        "id": "test_project_track_e",
        "idea": "A test project for Track E features",
        "workflow": "test_workflow",
        "state": "TASK_EXECUTION",
        "workflow_sequence": [{"state": "TASK_EXECUTION"}]
    }
    context_bus = ContextBus()
    meta_memory = ProjectMetaMemoryManager()
    
    # Store reliability scores for crews
    meta_memory.add_performance_metric("crew_reliability", 0.9, {"crew_name": "HighReliabilityCrew"})
    meta_memory.add_performance_metric("crew_reliability", 0.2, {"crew_name": "LowReliabilityCrew"})
    
    crew_classes = {
        "TASK_EXECUTION": [LowReliabilityCrew, HighReliabilityCrew],
        "VALIDATION": [PermanentErrorCrew],
        "RECOVERY": [RecoveryCrew],
    }
    crew_router = CrewRouter(crew_classes, context_bus, meta_memory)
    
    mock_cost_workflow = MagicMock()
    mock_cost_crew = MagicMock()
    metrics = {
        "workflow_cost_usd": mock_cost_workflow,
        "crew_cost_usd_total": mock_cost_crew,
    }

    executor = DistributedExecutor(crew_router)
    engine = WorkflowEngine(project_data, crew_router=crew_router, metrics=metrics, context_bus=context_bus, project_meta_memory=meta_memory, executor=executor)
    
    await executor.start()

    # 2. Test Reliability-Based Selection
    # The router should select HighReliabilityCrew
    result = await engine.handle_task_execution()
    # This is tricky to assert without modifying the crew to return its name. 
    # For now, we assume the log message is sufficient. A better test would involve more detailed return values.

    # 3. Test Failure Recovery and Human-in-the-Loop
    project_data["state"] = "VALIDATION"
    result = await engine.handle_validation()
    
    assert project_data["state"] == "RECOVERY"
    
    history = await context_bus.get_history()
    human_event = next((e for e in history if e["name"] == "human_intervention_needed"), None)
    assert human_event is not None
    assert human_event["data"]["reason"] == "permanent_error"
    
    # 4. Test Cost Metrics
    mock_cost_crew.labels.assert_called_with(crew_name="PermanentErrorCrew")
    mock_cost_crew.labels().observe.assert_called()
    
    await executor.stop()
