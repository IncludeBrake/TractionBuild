import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class WorkflowEngine:
    def __init__(self, project_data: Dict[str, Any], registry=None):
        self.project_data = project_data
        self.registry = registry
        logger.info(f"WorkflowEngine initialized for project {project_data.get('id')}")

    async def run(self) -> Dict[str, Any]:
        """Main entry point for running the workflow."""
        max_iterations = 20  # Safety limit to prevent infinite loops
        iterations = 0

        while iterations < max_iterations:
            current_state = self.project_data.get("state", "UNKNOWN")

            # Exit conditions
            if current_state in ["COMPLETED", "ERROR", "FAILED"]:
                logger.info(f"✅ Workflow terminated with state: {current_state}")
                break

            await self.route_and_execute()
            iterations += 1

        if iterations >= max_iterations:
            logger.error(f"⚠️ Workflow exceeded maximum iterations ({max_iterations})")
            self.project_data["state"] = "ERROR"
            self.project_data["message"] = "Workflow exceeded maximum iterations"

        return self.project_data

    async def route_and_execute(self) -> Dict[str, Any]:
        """Route to the correct state handler."""
        state = self.project_data.get("state", "UNKNOWN")
        logger.info(f"🔄 Routing workflow state: {state}")

        handlers = {
            "idea_validation": self.handle_idea_validation,
            "TASK_EXECUTION": self.handle_task_execution,
            "MARKETING_PREPARATION": self.handle_marketing_preparation,
            "VALIDATION": self.handle_validation,
            "LAUNCH": self.handle_launch,
            "IN_PROGRESS": self.handle_in_progress,
        }

        handler = handlers.get(state)
        if handler:
            return await handler()
        else:
            logger.warning(f"Unknown state: {state}")
            self.project_data["state"] = "ERROR"
            self.project_data["message"] = f"Unknown state: {state}"
            return self.project_data

    # === State Handlers ===

    async def handle_idea_validation(self) -> Dict[str, Any]:
        logger.info("💡 Validating idea...")
        self.project_data["state"] = "TASK_EXECUTION"
        self.project_data["message"] = "Idea validated successfully."
        return self.project_data

    async def handle_task_execution(self) -> Dict[str, Any]:
        logger.info("🧱 Executing build tasks...")
        # Placeholder for crew execution
        self.project_data["state"] = "MARKETING_PREPARATION"
        self.project_data["message"] = "Build phase completed."
        return self.project_data

    async def handle_marketing_preparation(self) -> Dict[str, Any]:
        logger.info("📣 Preparing marketing assets...")
        self.project_data["state"] = "VALIDATION"
        self.project_data["message"] = "Marketing prep complete."
        return self.project_data

    async def handle_validation(self) -> Dict[str, Any]:
        logger.info("✅ Validating deliverables...")
        self.project_data["state"] = "LAUNCH"
        self.project_data["message"] = "Validation passed."
        return self.project_data

    async def handle_launch(self) -> Dict[str, Any]:
        logger.info("🚀 Launching product...")
        self.project_data["state"] = "COMPLETED"
        self.project_data["message"] = "Launch successful!"
        return self.project_data

    async def handle_in_progress(self) -> Dict[str, Any]:
        logger.info("⏳ Continuing in-progress workflow...")
        self.project_data["state"] = "COMPLETED"
        self.project_data["message"] = "Workflow resumed and completed."
        return self.project_data
