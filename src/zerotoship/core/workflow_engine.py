import logging
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class WorkflowEngine:
    def __init__(self, project_data: Dict[str, Any], registry=None, crew_router=None, metrics: Optional[Dict[str, Any]] = None):
        self.project_data = project_data
        self.registry = registry
        self.crew_router = crew_router  # ✅ Store the router
        self.metrics = metrics or {}
        logger.info(f"WorkflowEngine initialized for project {project_data.get('id')}")

        # State handlers mapping
        self.state_handlers = {
            "IDEA_VALIDATION": self.handle_idea_validation,
            "TASK_EXECUTION": self.handle_task_execution,
            "MARKETING_PREPARATION": self.handle_marketing_preparation,
            "VALIDATION": self.handle_validation,
            "LAUNCH": self.handle_launch,
            "IN_PROGRESS": self.handle_in_progress,
            "COMPLETED": self.handle_completed,
        }

    async def run(self) -> Dict[str, Any]:
        """Main entry point for running the workflow."""
        # Increment workflow counter
        if "workflow_total" in self.metrics:
            self.metrics["workflow_total"].inc()

        # Track workflow duration
        start_time = time.time()

        max_iterations = 20  # Safety limit to prevent infinite loops
        iterations = 0

        while iterations < max_iterations:
            current_state = self.project_data.get("state", "UNKNOWN")

            # Exit conditions
            if current_state in ["COMPLETED", "ERROR", "FAILED"]:
                logger.info(f"✅ Workflow terminated with state: {current_state}")
                # Update final state gauge
                if "workflow_state" in self.metrics:
                    self.metrics["workflow_state"].labels(state=current_state).set(1)
                break

            await self.route_and_execute()
            iterations += 1

        if iterations >= max_iterations:
            logger.error(f"⚠️ Workflow exceeded maximum iterations ({max_iterations})")
            self.project_data["state"] = "ERROR"
            self.project_data["message"] = "Workflow exceeded maximum iterations"
            if "workflow_state" in self.metrics:
                self.metrics["workflow_state"].labels(state="ERROR").set(1)

        # Record workflow duration
        duration = time.time() - start_time
        if "workflow_duration_seconds" in self.metrics:
            self.metrics["workflow_duration_seconds"].observe(duration)
        logger.info(f"⏱️ Workflow completed in {duration:.2f} seconds")

        return self.project_data

    async def route_and_execute(self) -> Dict[str, Any]:
        """Route to the correct state handler."""
        state = self.project_data.get("state", "UNKNOWN")
        logger.info(f"🔄 Routing workflow state: {state}")

        # Update state gauge before executing handler
        if "workflow_state" in self.metrics:
            self.metrics["workflow_state"].labels(state=state).set(1)

        handler = self.state_handlers.get(state)
        if handler:
            return await handler()
        else:
            logger.warning(f"Unknown state: {state}")
            self.project_data["state"] = "ERROR"
            self.project_data["message"] = f"Unknown state: {state}"
            return self.project_data

    # === State Handlers ===

    async def handle_idea_validation(self) -> Dict[str, Any]:
        logger.info("💡 [WorkflowEngine] Entering IDEA_VALIDATION state")
        if self.crew_router:
            result = await self.crew_router.execute("IDEA_VALIDATION", self.project_data)

            if result.get("status") == "success":
                if "data" in result:
                    self.project_data.update(result["data"])
                self.project_data["state"] = result.get("next_state", "TASK_EXECUTION")
                self.project_data["message"] = result.get("message", "Idea validated successfully.")
            else:
                logger.error(f"❌ Error in IDEA_VALIDATION: {result.get('message')}")
                self.project_data["state"] = "FAILED"
                self.project_data["message"] = result.get("message", "Validation failed")
        else:
            logger.warning("⚠️ No CrewRouter configured. Skipping IDEA_VALIDATION.")
            self.project_data["state"] = "TASK_EXECUTION"
            self.project_data["message"] = "Idea validation skipped (no crew router)"

        return self.project_data

    async def handle_task_execution(self) -> Dict[str, Any]:
        logger.info("⚙️ [WorkflowEngine] Entering TASK_EXECUTION state")
        if self.crew_router:
            # 1. Delegate to Router
            result = await self.crew_router.execute("TASK_EXECUTION", self.project_data)

            # 2. Update Project Data with Crew Output
            if result.get("status") == "success":
                if "data" in result:
                    self.project_data.update(result["data"])

                # 3. Determine Next State (Allow crew to dictate, or fallback to default)
                self.project_data["state"] = result.get("next_state", "MARKETING_PREPARATION")
                self.project_data["message"] = result.get("message", "Build phase completed.")
            else:
                logger.error(f"❌ Error in TASK_EXECUTION: {result.get('message')}")
                self.project_data["state"] = "FAILED"
                self.project_data["message"] = result.get("message", "Build execution failed")
        else:
            logger.warning("⚠️ No CrewRouter configured. Skipping execution.")
            self.project_data["state"] = "MARKETING_PREPARATION"
            self.project_data["message"] = "Task execution skipped (no crew router)"

        return self.project_data

    async def handle_marketing_preparation(self) -> Dict[str, Any]:
        logger.info("📣 [WorkflowEngine] Entering MARKETING_PREPARATION state")
        if self.crew_router:
            result = await self.crew_router.execute("MARKETING_PREPARATION", self.project_data)

            if result.get("status") == "success":
                if "data" in result:
                    self.project_data.update(result["data"])
                self.project_data["state"] = result.get("next_state", "VALIDATION")
                self.project_data["message"] = result.get("message", "Marketing prep complete.")
            else:
                logger.error(f"❌ Error in MARKETING_PREPARATION: {result.get('message')}")
                self.project_data["state"] = "FAILED"
                self.project_data["message"] = result.get("message", "Marketing preparation failed")
        else:
            logger.warning("⚠️ No CrewRouter configured. Skipping marketing preparation.")
            self.project_data["state"] = "VALIDATION"
            self.project_data["message"] = "Marketing preparation skipped (no crew router)"

        return self.project_data

    async def handle_validation(self) -> Dict[str, Any]:
        logger.info("🛡️ [WorkflowEngine] Entering VALIDATION state")
        if self.crew_router:
            result = await self.crew_router.execute("VALIDATION", self.project_data)

            if result.get("status") == "success":
                if "data" in result:
                    self.project_data.update(result["data"])
                self.project_data["state"] = result.get("next_state", "LAUNCH")
                self.project_data["message"] = result.get("message", "Validation passed.")
            else:
                logger.error(f"❌ Error in VALIDATION: {result.get('message')}")
                self.project_data["state"] = "FAILED"
                self.project_data["message"] = result.get("message", "Validation failed")
        else:
            logger.warning("⚠️ No CrewRouter configured. Skipping validation.")
            self.project_data["state"] = "LAUNCH"
            self.project_data["message"] = "Validation skipped (no crew router)"

        return self.project_data

    async def handle_launch(self) -> Dict[str, Any]:
        logger.info("🚀 [WorkflowEngine] Entering LAUNCH state")
        if self.crew_router:
            result = await self.crew_router.execute("LAUNCH", self.project_data)

            if result.get("status") == "success":
                if "data" in result:
                    self.project_data.update(result["data"])
                self.project_data["state"] = result.get("next_state", "COMPLETED")
                self.project_data["message"] = result.get("message", "Launch successful!")
            else:
                logger.error(f"❌ Error in LAUNCH: {result.get('message')}")
                self.project_data["state"] = "FAILED"
                self.project_data["message"] = result.get("message", "Launch failed")
        else:
            logger.warning("⚠️ No CrewRouter configured. Skipping launch.")
            self.project_data["state"] = "COMPLETED"
            self.project_data["message"] = "Launch skipped (no crew router)"

        return self.project_data

    async def handle_in_progress(self) -> Dict[str, Any]:
        logger.info("⏳ [WorkflowEngine] Entering IN_PROGRESS state")
        if self.crew_router:
            result = await self.crew_router.execute("IN_PROGRESS", self.project_data)

            if result.get("status") == "success":
                if "data" in result:
                    self.project_data.update(result["data"])
                self.project_data["state"] = result.get("next_state", "COMPLETED")
                self.project_data["message"] = result.get("message", "Workflow resumed and completed.")
            else:
                logger.error(f"❌ Error in IN_PROGRESS: {result.get('message')}")
                self.project_data["state"] = "FAILED"
                self.project_data["message"] = result.get("message", "In-progress workflow failed")
        else:
            logger.warning("⚠️ No CrewRouter configured. Completing workflow.")
            self.project_data["state"] = "COMPLETED"
            self.project_data["message"] = "Workflow resumed and completed (no crew router)"

        return self.project_data

    async def handle_completed(self) -> Dict[str, Any]:
        logger.info("✅ [WorkflowEngine] Workflow COMPLETED")
        self.project_data["message"] = "Workflow completed successfully"
        return self.project_data
