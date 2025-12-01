import asyncio
from typing import Dict, Any, Callable
from ..schemas.core import ProjectStatus
from .agent_registry import AgentRegistry



class WorkflowEngine:
    def __init__(self, registry: AgentRegistry, step_timeout: int = 300):
        self.r = registry
        self.t = step_timeout

    async def _step(self, fn: Callable[[], Any], timeout: int) -> Any:
        return await asyncio.wait_for(fn(), timeout=timeout)

    async def run(self, project: Dict[str, Any]) -> Dict[str, Any]:
        ctx: Dict[str, Any] = {"project": project, "artifacts": {}}
        order = ["validator", "advisory"]
        for key in order:
            agent = self.r.get(key)
            # adapt to our adapter interface: agent.run(ctx)
            res = await self._step(lambda: agent.run(ctx), timeout=self.t)
            ctx["artifacts"][key] = res
        ctx["project"]["state"] = ProjectStatus.COMPLETED.value
        return ctx
