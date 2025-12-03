"""
CrewRouter - Centralized dispatcher for crew execution.
Unifies how WorkflowEngine calls crews and handles errors consistently.
"""

import logging
import asyncio
import yaml
from typing import Dict, Any, Optional, List
from .context_bus import ContextBus
from .project_meta_memory import ProjectMetaMemoryManager

logger = logging.getLogger(__name__)

class CrewRouter:
    """Routes workflow states to appropriate crew implementations."""

    def __init__(self, crew_classes: Dict[str, List[Any]], context_bus: ContextBus, project_meta_memory: ProjectMetaMemoryManager):
        """Initialize the router with a mapping of states to crew classes.

        Args:
            crew_classes: Dictionary mapping state names to lists of crew classes
            context_bus: The shared context bus instance.
            project_meta_memory: The project meta memory manager.
        """
        self.crew_classes = crew_classes
        self.context_bus = context_bus
        self.project_meta_memory = project_meta_memory
        self.crew_workers = {crew_name: 1 for crew_name in self.crew_classes.keys()}
        
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

        logger.info(f"CrewRouter initialized with {len(crew_classes)} crew mappings")

    async def _get_crew_reliability(self, crew_class: Any) -> float:
        # Simplified reliability check. A real implementation would be more complex.
        crew_name = crew_class.__name__
        entries = self.project_meta_memory.get_memory_entries(
            memory_type="performance_metric",
            tags={f"crew:{crew_name}", "reliability"}
        )
        if not entries:
            return 0.5 # Default reliability
        return entries[0].content.get("value", 0.5)

    async def execute(self, state: str, context: Dict[str, Any], project_data: Dict[str, Any]) -> tuple[Dict[str, Any], str]:
        """Selects and executes the most reliable crew for the given state."""
        candidate_classes = self.crew_classes.get(state)
        if not candidate_classes:
            logger.warning(f"No crew registered for state: {state}")
            return {"status": "skipped", "message": f"No crew for {state}"}, ""

        # E2: Reliability-Based Crew Selection
        if len(candidate_classes) > 1:
            reliabilities = await asyncio.gather(*[self._get_crew_reliability(c) for c in candidate_classes])
            max_reliability = max(reliabilities)
            if max_reliability < 0.5: # E7: Human-in-the-Loop Feedback
                logger.warning(f"No reliable crew found for state {state}. Max reliability: {max_reliability:.2f}. Requesting human intervention.")
                await self.context_bus.record("human_intervention_needed", {"state": state, "reason": "low_crew_reliability"})
            
            best_crew_class = candidate_classes[reliabilities.index(max_reliability)]
            logger.info(f"Selected crew {best_crew_class.__name__} for state {state} based on reliability.")
        else:
            best_crew_class = candidate_classes[0]

        crew = best_crew_class(project_data)
        selected_crew_name = best_crew_class.__name__

        # D3: Dynamic Crew Scaling (logic remains the same)
        # ... (scaling logic here)

        logger.info(f"🚀 Dispatching crew for state: {state} with crew {crew.__class__.__name__}")
        try:
            result = await crew.run(context)
            logger.info(f"✅ Crew execution completed for state: {state}")
            return result, selected_crew_name
        except Exception as e:
            logger.exception(f"Crew execution failed for {state}: {e}")
            return {"status": "error", "message": str(e), "error_type": type(e).__name__}, selected_crew_name
