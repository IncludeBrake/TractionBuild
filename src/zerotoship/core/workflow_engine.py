import logging
import time
import yaml
import asyncio
from typing import Dict, Any, Optional
from .context_bus import ContextBus
from .learning_memory import LearningMemory
from .temporal_memory import TemporalMemory
from .distributed_executor import DistributedExecutor
from .project_meta_memory import ProjectMetaMemoryManager, MemoryType
from ..utils.context_exporter import export_context_to_graph

logger = logging.getLogger(__name__)

def _estimate_cost(token_usage: int) -> float:
    """A placeholder function to estimate cost based on token usage."""
    # This is a simplified estimation. A real implementation would be more complex.
    # e.g., based on different models and their pricing.
    return (token_usage / 1000) * 0.002 # A sample rate of $0.002 per 1K tokens

class WorkflowEngine:
    def __init__(self, project_data: Dict[str, Any], registry=None, crew_router=None, metrics: Optional[Dict[str, Any]] = None, memory: Optional[LearningMemory] = None, context_bus: Optional[ContextBus] = None, project_meta_memory: Optional[ProjectMetaMemoryManager] = None, executor: Optional[DistributedExecutor] = None):
        self.project_data = project_data
        self.registry = registry
        self.crew_router = crew_router
        self.metrics = metrics or {}
        self.context = context_bus or ContextBus()
        self.memory = memory or LearningMemory()
        self.project_meta_memory = project_meta_memory or ProjectMetaMemoryManager()
        self.executor = executor
        self.temporal_memory = TemporalMemory() # For recording events for replay
        self.total_cost = 0
        
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
            "RECOVERY": self.handle_recovery, # E6: Add recovery handler
        }

    async def run(self) -> Dict[str, Any]:
        """Main entry point for running the workflow."""
        # Increment workflow counter
        if "workflow_total" in self.metrics:
            self.metrics["workflow_total"].inc()

        # Track workflow duration
        start_time = time.time()

        # E1: Hybrid Memory Integration
        meta_memories = []
        if self.project_meta_memory:
            meta_memories.extend(self.project_meta_memory.get_memory_entries(memory_type="heuristic", limit=2))
            meta_memories.extend(self.project_meta_memory.get_memory_entries(memory_type="success_pattern", limit=1))
        
        if meta_memories:
            logger.info(f"🧠 Found {len(meta_memories)} meta memories from ProjectMetaMemory.")
            await self.context.set("meta_memories", [m.to_dict() for m in meta_memories])

        # C2: Search for related projects from past runs (fallback)
        idea = self.project_data.get("idea", "")
        related = await self.memory.search(idea, limit=3)
        logger.info(f"🧠 Found {len(related)} related concepts from LearningMemory.")

        # C3: Inject related projects into ContextBus
        all_related = [m.content for m in meta_memories] + related
        await self.context.set("related_projects", all_related)
        if all_related:
            if "memory_hits_total" in self.metrics:
                self.metrics["memory_hits_total"].inc()
            logger.info(f"📚 Found a total of {len(all_related)} related memories.")

        # E4: Dynamic Workflow Reconfiguration
        await self._reconfigure_workflow()

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
        if "workflow_cost_usd" in self.metrics:
            self.metrics["workflow_cost_usd"].observe(self.total_cost)
        logger.info(f"⏱️ Workflow completed in {duration:.2f} seconds with a total estimated cost of ${self.total_cost:.4f}")

        # B7: Store workflow metrics in context
        await self.context.set("workflow_metrics", {
            "duration_sec": duration,
            "total_states": iterations,
            "final_state": self.project_data.get("state")
        })

        # B5: Add final context snapshot to project output
        final_context = await self.context.snapshot()
        self.project_data["final_context"] = final_context
        self.project_data["event_history"] = await self.context.get_history()
        logger.info(f"📊 Final context has {await self.context.size()} keys")

        # B8: Persist context snapshot if registry is available
        if self.registry:
            project_id = self.project_data.get("id", "unknown")
            await self.registry.save_snapshot(project_id, final_context)

        # C5: Add final context and event history to learning memory
        project_id = self.project_data.get("id", "unknown")
        idea = self.project_data.get("idea", "")
        final_state = self.project_data.get("state")
        await self.memory.add(project_id, idea, final_state)
        logger.info(f"🧠 Added/updated project '{idea}' in learning memory with status {final_state}.")

        # D5: Export context graph
        output_dir = f"output/{project_id}"
        await export_context_to_graph(self.context, output_dir)
        
        # D6: Persist learning memory
        await self.memory.persist()
        logger.info("🧠 Learning memory persisted.")

        return self.project_data

    async def _reconfigure_workflow(self):
        """Dynamically reconfigures the workflow based on memory and reliability."""
        idea = self.project_data.get("idea", "")
        entry = next((e for e in self.memory._entries if e["text"] == idea), None)
        
        if entry and entry["reliability_score"] > 0.8:
            sequence = self.project_data.get("workflow_sequence", [])
            if "VALIDATION" in [step['state'] for step in sequence]:
                logger.info("📈 High reliability score detected. Skipping VALIDATION step.")
                self.project_data["workflow_sequence"] = [step for step in sequence if step['state'] != "VALIDATION"]

    def _get_next_state_from_sequence(self, current_state: str) -> str:
        """Gets the next state from the workflow sequence."""
        sequence = self.project_data.get("workflow_sequence", [])
        try:
            current_index = [i for i, step in enumerate(sequence) if step['state'] == current_state][0]
            return sequence[current_index + 1]['state']
        except (IndexError, ValueError):
            return "COMPLETED"

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

    async def _execute_crew_with_feedback(self, state_name: str) -> Dict[str, Any]:
        """Execute a crew with retry logic and record feedback."""
        # E3: Fetch and merge external data before crew execution
        await self.context.fetch_and_merge_external_data()

        context_snapshot = await self.context.snapshot()
        context_snapshot.update(self.project_data)

        max_retries = self.adaptive_config.get("retry_limit", 3)
        
        for attempt in range(max_retries):
            start_time = time.time()
            result, selected_crew_name = await self.executor.schedule(state_name, context_snapshot, self.project_data)
            duration = time.time() - start_time
            status = result.get("status", "error")

            feedback = { "status": status, "duration_seconds": duration, "error_type": result.get("message") if status != "success" else None }
            
            # Store feedback history for each attempt
            feedback_history_key = f"{state_name}_feedback_history"
            history = await self.context.get(feedback_history_key) or []
            history.append(feedback)
            await self.context.set(feedback_history_key, history)

            # E2: Store crew reliability in ProjectMetaMemory
            if self.project_meta_memory:
                successes = len([item for item in history if item["status"] == "success"])
                reliability_score = successes / len(history) if history else 0.5
                self.project_meta_memory.add_performance_metric(
                    "crew_reliability", 
                    reliability_score, 
                    {"crew_name": selected_crew_name}
                )

            # E5: Cost Optimization Metrics
            token_usage = result.get("token_usage", 0)
            cost = _estimate_cost(token_usage)
            self.total_cost += cost
            if "crew_cost_usd_total" in self.metrics:
                self.metrics["crew_cost_usd_total"].labels(crew_name=selected_crew_name).observe(cost)
            
            # Record Prometheus metrics for each attempt
            if "crew_duration_seconds" in self.metrics:
                self.metrics["crew_duration_seconds"].labels(crew_name=selected_crew_name).observe(duration)

            if status == "success":
                logger.info(f"📝 Recorded feedback for {state_name} (attempt {attempt+1}): status={status}, duration={duration:.2f}s")
                return result

            # If not success, record failure and decide whether to retry
            if "crew_failures_total" in self.metrics:
                self.metrics["crew_failures_total"].labels(crew_name=selected_crew_name).inc()
            
            # E6: Error Categorization
            if result.get("error_category") == "permanent":
                logger.error(f"Permanent error in {state_name}. Re-routing to RECOVERY state.")
                await self.context.record("human_intervention_needed", {"state": state_name, "reason": "permanent_error", "error": result.get("message")})
                self.project_data["state"] = "RECOVERY"
                self.project_data["recovery_from_state"] = state_name
                await self.context.record(f"{state_name}_permanent_failure", feedback)
                return result # Stop retrying on permanent error

            if attempt < max_retries - 1:
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed for {state_name}. Retrying...")
                await asyncio.sleep(2 ** attempt) # Exponential backoff
            else:
                logger.error(f"All {max_retries} attempts failed for {state_name}.")
                await self.context.record(f"{state_name}_failed_retry", feedback)
        
        return result

    async def handle_idea_validation(self) -> Dict[str, Any]:
        logger.info("💡 [WorkflowEngine] Entering IDEA_VALIDATION state")
        if self.crew_router:
            result = await self._execute_crew_with_feedback("IDEA_VALIDATION")

            if result.get("status") == "success":
                if "data" in result:
                    self.project_data.update(result["data"])
                    await self.context.merge(result["data"])

                self.project_data["state"] = self._get_next_state_from_sequence("IDEA_VALIDATION")
                self.project_data["message"] = result.get("message", "Idea validated successfully.")
                await self.context.record("IDEA_VALIDATION_executed", result)
            elif self.project_data.get("state") != "RECOVERY":
                logger.error(f"❌ Error in IDEA_VALIDATION: {result.get('message')}")
                self.project_data["state"] = "FAILED"
                self.project_data["message"] = result.get("message", "Validation failed")
                await self.context.record("IDEA_VALIDATION_failed", result)
        else:
            logger.warning("⚠️ No CrewRouter configured. Skipping IDEA_VALIDATION.")
            self.project_data["state"] = self._get_next_state_from_sequence("IDEA_VALIDATION")
            self.project_data["message"] = "Idea validation skipped (no crew router)"

        return self.project_data

    async def handle_task_execution(self) -> Dict[str, Any]:
        logger.info("⚙️ [WorkflowEngine] Entering TASK_EXECUTION state")
        if self.crew_router:
            result = await self._execute_crew_with_feedback("TASK_EXECUTION")

            # 3. Update Project Data with Crew Output
            if result.get("status") == "success":
                if "data" in result:
                    self.project_data.update(result["data"])
                    # Merge crew outputs into shared context
                    await self.context.merge(result["data"])

                # 4. Determine Next State (Allow crew to dictate, or fallback to default)
                self.project_data["state"] = self._get_next_state_from_sequence("TASK_EXECUTION")
                self.project_data["message"] = result.get("message", "Build phase completed.")

                # 5. Record event in history
                await self.context.record("TASK_EXECUTION_executed", result)
            elif self.project_data.get("state") != "RECOVERY":
                logger.error(f"❌ Error in TASK_EXECUTION: {result.get('message')}")
                self.project_data["state"] = "FAILED"
                self.project_data["message"] = result.get("message", "Build execution failed")
                await self.context.record("TASK_EXECUTION_failed", result)
        else:
            logger.warning("⚠️ No CrewRouter configured. Skipping execution.")
            self.project_data["state"] = self._get_next_state_from_sequence("TASK_EXECUTION")
            self.project_data["message"] = "Task execution skipped (no crew router)"

        return self.project_data

    async def handle_marketing_preparation(self) -> Dict[str, Any]:
        logger.info("📣 [WorkflowEngine] Entering MARKETING_PREPARATION state")
        if self.crew_router:
            result = await self._execute_crew_with_feedback("MARKETING_PREPARATION")

            if result.get("status") == "success":
                if "data" in result:
                    self.project_data.update(result["data"])
                    await self.context.merge(result["data"])

                self.project_data["state"] = self._get_next_state_from_sequence("MARKETING_PREPARATION")
                self.project_data["message"] = result.get("message", "Marketing prep complete.")
                await self.context.record("MARKETING_PREPARATION_executed", result)
            elif self.project_data.get("state") != "RECOVERY":
                logger.error(f"❌ Error in MARKETING_PREPARATION: {result.get('message')}")
                self.project_data["state"] = "FAILED"
                self.project_data["message"] = result.get("message", "Marketing preparation failed")
                await self.context.record("MARKETING_PREPARATION_failed", result)
        else:
            logger.warning("⚠️ No CrewRouter configured. Skipping marketing preparation.")
            self.project_data["state"] = self._get_next_state_from_sequence("MARKETING_PREPARATION")
            self.project_data["message"] = "Marketing preparation skipped (no crew router)"

        return self.project_data

    async def handle_validation(self) -> Dict[str, Any]:
        logger.info("🛡️ [WorkflowEngine] Entering VALIDATION state")
        if self.crew_router:
            result = await self._execute_crew_with_feedback("VALIDATION")

            if result.get("status") == "success":
                if "data" in result:
                    self.project_data.update(result["data"])
                    await self.context.merge(result["data"])

                self.project_data["state"] = self._get_next_state_from_sequence("VALIDATION")
                self.project_data["message"] = result.get("message", "Validation passed.")
                await self.context.record("VALIDATION_executed", result)
            elif self.project_data.get("state") != "RECOVERY":
                logger.error(f"❌ Error in VALIDATION: {result.get('message')}")
                self.project_data["state"] = "FAILED"
                self.project_data["message"] = result.get("message", "Validation failed")
                await self.context.record("VALIDATION_failed", result)
        else:
            logger.warning("⚠️ No CrewRouter configured. Skipping validation.")
            self.project_data["state"] = self._get_next_state_from_sequence("VALIDATION")
            self.project_data["message"] = "Validation skipped (no crew router)"

        return self.project_data

    async def handle_launch(self) -> Dict[str, Any]:
        logger.info("🚀 [WorkflowEngine] Entering LAUNCH state")
        if self.crew_router:
            result = await self._execute_crew_with_feedback("LAUNCH")

            if result.get("status") == "success":
                if "data" in result:
                    self.project_data.update(result["data"])
                    await self.context.merge(result["data"])

                self.project_data["state"] = self._get_next_state_from_sequence("LAUNCH")
                self.project_data["message"] = result.get("message", "Launch successful!")
                await self.context.record("LAUNCH_executed", result)
            elif self.project_data.get("state") != "RECOVERY":
                logger.error(f"❌ Error in LAUNCH: {result.get('message')}")
                self.project_data["state"] = "FAILED"
                self.project_data["message"] = result.get("message", "Launch failed")
                await self.context.record("LAUNCH_failed", result)
        else:
            logger.warning("⚠️ No CrewRouter configured. Skipping launch.")
            self.project_data["state"] = self._get_next_state_from_sequence("LAUNCH")
            self.project_data["message"] = "Launch skipped (no crew router)"

        return self.project_data


    async def handle_in_progress(self) -> Dict[str, Any]:
        logger.info("⏳ [WorkflowEngine] Entering IN_PROGRESS state")
        if self.crew_router:
            result = await self._execute_crew_with_feedback("IN_PROGRESS")

            if result.get("status") == "success":
                if "data" in result:
                    self.project_data.update(result["data"])
                    await self.context.merge(result["data"])

                self.project_data["state"] = result.get("next_state", "COMPLETED")
                self.project_data["message"] = result.get("message", "Workflow resumed and completed.")
                await self.context.record("IN_PROGRESS_executed", result)
            elif self.project_data.get("state") != "RECOVERY":
                logger.error(f"❌ Error in IN_PROGRESS: {result.get('message')}")
                self.project_data["state"] = "FAILED"
                self.project_data["message"] = result.get("message", "In-progress workflow failed")
                await self.context.record("IN_PROGRESS_failed", result)
        else:
            logger.warning("⚠️ No CrewRouter configured. Completing workflow.")
            self.project_data["state"] = "COMPLETED"
            self.project_data["message"] = "Workflow resumed and completed (no crew router)"

        return self.project_data

    async def handle_completed(self) -> Dict[str, Any]:
        logger.info("✅ [WorkflowEngine] Workflow COMPLETED")
        self.project_data["message"] = "Workflow completed successfully"
        return self.project_data

    async def handle_recovery(self) -> Dict[str, Any]:
        """Handles permanent failures by routing to a recovery crew."""
        logger.warning(f"Entering RECOVERY state from {self.project_data.get('recovery_from_state')}")
        
        # In a real implementation, a specialized RecoveryCrew would be executed.
        # For now, we will just log the event and move to a FAILED state.
        self.project_data["state"] = "FAILED"
        self.project_data["message"] = "Permanent failure. Recovery measures would be initiated here."
        await self.context.record("RECOVERY_initiated", {"from_state": self.project_data.get("recovery_from_state")})
        return self.project_data
