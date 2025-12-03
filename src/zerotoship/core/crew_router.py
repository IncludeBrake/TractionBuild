"""
CrewRouter - Centralized dispatcher for crew execution.
Unifies how WorkflowEngine calls crews and handles errors consistently.
"""

import logging
import asyncio
import yaml
from typing import Dict, Any, Optional
from .context_bus import ContextBus

logger = logging.getLogger(__name__)

class CrewRouter:
    """Routes workflow states to appropriate crew implementations."""

    def __init__(self, crews: Dict[str, Any], context_bus: ContextBus):
        """Initialize the router with a mapping of states to crew instances.

        Args:
            crews: Dictionary mapping state names to crew instances
                   Example: {"TASK_EXECUTION": BuilderCrew(project_data)}
            context_bus: The shared context bus instance.
        """
        self.crews = crews
        self.context_bus = context_bus
        self.crew_workers = {crew_name: 1 for crew_name in self.crews.keys()}
        
        # Load adaptive config
        try:
            with open("config/adaptive_config.yaml", 'r') as f:
                self.adaptive_config = yaml.safe_load(f)
        except FileNotFoundError:
            self.adaptive_config = {
                "retry_limit": 3,
                "scaling_thresholds": {"up": 2.0, "down": 10.0},
                "reliability_decay": 0.95
            }
            logger.warning("adaptive_config.yaml not found. Using default values.")

        logger.info(f"CrewRouter initialized with {len(crews)} crew mappings")

    async def execute(self, state: str, context: Dict[str, Any], project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the crew associated with the given state."""
        crew_or_class = self.crews.get(state)
        if not crew_or_class:
            logger.warning(f"No crew registered for state: {state}")
            return {
                "status": "skipped",
                "message": f"No crew for {state}",
                "data": {},
                "next_state": None,
            }
        
        # Instantiate crew if it's a class, otherwise use the instance directly
        if isinstance(crew_or_class, type): # Check if it's a class
            crew = crew_or_class(project_data)
        else:
            crew = crew_or_class

        # D3: Dynamic Crew Scaling
        feedback_history_key = f"{state}_feedback_history"
        history = await self.context_bus.get(feedback_history_key) or []
        
        if history:
            durations = [item['duration_seconds'] for item in history]
            avg_duration = sum(durations) / len(durations)
            
            num_workers = self.crew_workers.get(state, 1)
            thresholds = self.adaptive_config.get("scaling_thresholds", {"up": 2.0, "down": 10.0})
            
            if avg_duration < thresholds["up"]:
                num_workers += 1
                logger.info(f"📈 Scaling up workers for {state} to {num_workers} due to fast avg duration ({avg_duration:.2f}s)")
            elif avg_duration > thresholds["down"]:
                num_workers = max(1, num_workers - 1)
                logger.info(f"📉 Scaling down workers for {state} to {num_workers} due to slow avg duration ({avg_duration:.2f}s)")
            self.crew_workers[state] = num_workers

            self.crew_workers[state] = num_workers

        logger.info(f"🚀 Dispatching crew for state: {state}")
        try:
            # result = await crew.run(context, num_workers=self.crew_workers.get(state, 1))
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
