"""
CrewRouter - Centralized dispatcher for crew execution.
Unifies how WorkflowEngine calls crews and handles errors consistently.
"""

import logging
import asyncio
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class CrewRouter:
    """Routes workflow states to appropriate crew implementations."""

    def __init__(self, crews: Dict[str, Any]):
        """Initialize the router with a mapping of states to crew instances.

        Args:
            crews: Dictionary mapping state names to crew instances
                   Example: {"TASK_EXECUTION": BuilderCrew(project_data)}
        """
        self.crews = crews
        logger.info(f"CrewRouter initialized with {len(crews)} crew mappings")

    async def execute(self, state: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the crew associated with the given state.

        Args:
            state: The workflow state to execute
            context: Execution context dictionary

        Returns:
            Standardized crew result dictionary with status, message, and data
        """
        crew = self.crews.get(state)
        if not crew:
            logger.warning(f"No crew registered for state: {state}")
            return {
                "status": "skipped",
                "message": f"No crew for {state}",
                "data": {},
                "next_state": None,
            }

        logger.info(f"🚀 Dispatching crew for state: {state}")
        try:
            result = await crew.run(context)
            logger.info(f"✅ Crew execution completed for state: {state}")
            return result
        except Exception as e:
            logger.exception(f"Crew execution failed for {state}: {e}")
            return {
                "status": "error",
                "message": str(e),
                "data": {},
                "error_type": type(e).__name__,
                "next_state": "ERROR",
            }
