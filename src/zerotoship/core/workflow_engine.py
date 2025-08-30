import asyncio
import logging
from typing import Dict, Any
from ..schemas import ProjectStatus

logger = logging.getLogger(__name__)

class WorkflowEngine:
    def __init__(self, registry, step_timeout=300):
        self.registry = registry
        self.step_timeout = step_timeout
    
    async def run(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """Run the validation_and_launch workflow: Validator → AdvisoryBoard → COMPLETED."""
        ctx = {"project": project, "artifacts": {}}
        
        try:
            # Step 1: Validator
            logger.info(f"Starting validator for project {project.get('id', 'unknown')}")
            validator = self.registry.get("validator")
            if not validator:
                raise ValueError("Validator agent not found in registry")
            
            validation_result = await asyncio.wait_for(
                validator.run(ctx), 
                timeout=self.step_timeout
            )
            ctx["artifacts"]["validator"] = validation_result
            logger.info(f"Validator completed for project {project.get('id', 'unknown')}")
            
            # Step 2: Advisory Board
            logger.info(f"Starting advisory board for project {project.get('id', 'unknown')}")
            advisory = self.registry.get("advisory")
            if not advisory:
                raise ValueError("Advisory agent not found in registry")
            
            advisory_result = await asyncio.wait_for(
                advisory.run(ctx),
                timeout=self.step_timeout
            )
            ctx["artifacts"]["advisory"] = advisory_result
            logger.info(f"Advisory board completed for project {project.get('id', 'unknown')}")
            
            # Mark as completed
            ctx["project"]["state"] = ProjectStatus.COMPLETED.value
            
            return ctx
            
        except asyncio.TimeoutError:
            logger.error(f"Workflow timeout for project {project.get('id', 'unknown')}")
            ctx["project"]["state"] = ProjectStatus.ERROR.value
            ctx["error"] = "Workflow timeout"
            return ctx
        except Exception as e:
            logger.error(f"Workflow error for project {project.get('id', 'unknown')}: {str(e)}")
            ctx["project"]["state"] = ProjectStatus.ERROR.value
            ctx["error"] = str(e)
            return ctx
