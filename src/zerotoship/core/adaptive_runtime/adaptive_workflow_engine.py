from .adaptive_memory_manager import AdaptiveMemoryManager
from .reliability_router import ReliabilityRouter
from .recovery_crew import RecoveryCrew
from .cost_metrics import estimate_cost

class AdaptiveWorkflowEngine(WorkflowEngine):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.memory = AdaptiveMemoryManager()
        self.router = ReliabilityRouter()

    async def _execute_crew_with_feedback(self, state_name):
        try:
            result = await self.router.execute(state_name, self.context_bus.snapshot())
            cost = estimate_cost(result.get("token_usage", 0))
            self.metrics.observe("workflow_cost_usd", cost)
            self.memory.record_outcome(result)
            return result
        except Exception:
            recovery = RecoveryCrew(self.project_data)
            return await recovery.run(self.context_bus.snapshot())

