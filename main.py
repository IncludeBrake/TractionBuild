import asyncio
import uuid
import yaml
import logging
import os
import argparse
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import json

# Gracefully import Prometheus for optional monitoring
try:
    from prometheus_client import Summary, Counter, Gauge, Histogram, start_http_server
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

# Import ZeroToShip components
from src.zerotoship.core.workflow_engine import WorkflowEngine
from src.zerotoship.database.project_registry import ProjectRegistry
from src.zerotoship.core.config_generator import initialize_system

# ✅ Import Crews and Router
from src.zerotoship.crews.builder_crew import BuilderCrew
from src.zerotoship.crews.validator_crew import ValidatorCrew
from src.zerotoship.crews.marketing_crew import MarketingCrew
from src.zerotoship.crews.launch_crew import LaunchCrew
from src.zerotoship.crews.feedback_crew import FeedbackCrew
from src.zerotoship.core.crew_router import CrewRouter

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Prometheus Metrics Definition ---
if PROMETHEUS_AVAILABLE:
    REQUEST_TIME = Summary('zerotoship_request_processing_seconds', 'Time spent processing a workflow')
    WORKFLOW_EXECUTIONS = Counter('zerotoship_workflow_executions_total', 'Total workflow executions', ['workflow_name', 'status'])
    PROJECT_CREATIONS = Counter('zerotoship_project_creations_total', 'Total project creations', ['workflow_name'])
    ERROR_COUNTER = Counter('zerotoship_errors_total', 'Total errors', ['error_type'])

    # Enhanced metrics for workflow monitoring
    WORKFLOW_TOTAL = Counter('workflow_total', 'Total number of workflows run')
    WORKFLOW_STATE = Gauge('workflow_state', 'Current workflow state', ['state'])
    WORKFLOW_DURATION_SECONDS = Histogram('workflow_duration_seconds', 'Workflow execution duration in seconds', buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0])
else:
    # If Prometheus is not installed, these metrics do nothing.
    class MockMetric:
        def time(self): return self
        def inc(self, **_): pass
        def dec(self, **_): pass
        def set(self, *_, **__): pass
        def observe(self, *_, **__): pass
        def labels(self, **_): return self
    REQUEST_TIME = WORKFLOW_EXECUTIONS = PROJECT_CREATIONS = ERROR_COUNTER = WORKFLOW_TOTAL = WORKFLOW_STATE = WORKFLOW_DURATION_SECONDS = MockMetric()


class ZeroToShipOrchestrator:
    """The main orchestrator service for the ZeroToShip platform."""
    
    def __init__(self):
        self.workflows = self._load_workflows()
        self.registry = ProjectRegistry() # Connection details are handled by the registry
        if PROMETHEUS_AVAILABLE:
            try:
                start_http_server(8010)
                logger.info("Prometheus metrics server started on port 8010.")
            except OSError:
                logger.warning("Port 8010 is already in use. Prometheus server not started.")

    def _load_workflows(self) -> Dict[str, Any]:
        try:
            with open("config/workflows.yaml", 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error("FATAL: config/workflows.yaml not found. Cannot operate.")
            return {}

    async def __aenter__(self):
        await self.registry.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.registry.__aexit__(exc_type, exc, tb)

    async def run_project(self, idea: str, workflow_name: str) -> Dict[str, Any]:
        """Creates and executes a project workflow from start to finish."""
        project_data = {}
        try:
            with REQUEST_TIME.time():
                project_data = self._create_project_data(idea, workflow_name)
                
                PROJECT_CREATIONS.labels(workflow_name=workflow_name).inc()
                logger.info(f"Created project '{project_data['id']}' for workflow '{workflow_name}'.")

                # ✅ 1. Instantiate the Crews (passing project_data)
                logger.info("Initializing crews for workflow execution...")
                builder = BuilderCrew(project_data)
                validator = ValidatorCrew(project_data)
                marketing = MarketingCrew(project_data)
                launch = LaunchCrew(project_data)
                feedback = FeedbackCrew(project_data)

                # ✅ 2. Create the Router Map
                crew_router = CrewRouter({
                    "IDEA_VALIDATION": validator,
                    "TASK_EXECUTION": builder,
                    "MARKETING_PREPARATION": marketing,
                    "VALIDATION": validator,
                    "LAUNCH": launch,
                    "FEEDBACK_COLLECTION": feedback,
                    "IN_PROGRESS": builder,  # Fallback for in-progress states
                })
                logger.info("CrewRouter initialized with 7 crew mappings")

                # ✅ 3. Pass metrics to WorkflowEngine
                metrics_dict = {
                    "workflow_total": WORKFLOW_TOTAL,
                    "workflow_state": WORKFLOW_STATE,
                    "workflow_duration_seconds": WORKFLOW_DURATION_SECONDS,
                }

                # ✅ 4. Create WorkflowEngine with Router
                engine = WorkflowEngine(
                    project_data=project_data,
                    registry=self.registry,
                    crew_router=crew_router,  # <--- Injected here
                    metrics=metrics_dict
                )
                logger.info("WorkflowEngine initialized with CrewRouter")

                final_project_data = await engine.run()

                WORKFLOW_EXECUTIONS.labels(workflow_name=workflow_name, status=final_project_data.get('state')).inc()
            
            await self._save_project_result(final_project_data)
            return final_project_data
        except Exception as e:
            logger.error(f"Project '{project_data.get('id')}' failed catastrophically: {e}", exc_info=True)
            ERROR_COUNTER.labels(error_type="project_execution").inc()
            WORKFLOW_EXECUTIONS.labels(workflow_name=workflow_name, status="catastrophic_failure").inc()
            raise

    def _create_project_data(self, idea: str, workflow_name: str) -> Dict[str, Any]:
        """Builds the initial project_data dictionary."""
        if workflow_name not in self.workflows:
            raise ValueError(f"Workflow '{workflow_name}' not found.")
        
        workflow = self.workflows[workflow_name]
        initial_state = workflow['sequence'][0].get('state') # Safely get state
        
        return {
            "id": f"project_{uuid.uuid4().hex[:8]}",
            "idea": idea,
            "workflow": workflow_name,
            "state": initial_state,
            "created_at": datetime.now().isoformat(),
            "metadata": workflow.get('metadata', {})
        }

    async def _save_project_result(self, result: Dict[str, Any]):
        """Saves the final project result to a file and the registry."""
        project_id = result.get('id', 'unknown')
        output_dir = Path(f"output/{project_id}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save to local file
        with open(output_dir / "final_result.json", 'w') as f:
            json.dump(result, f, indent=2, default=str)
        logger.info(f"Final project results saved to {output_dir}")

        # Save final state to registry
        await self.registry.save_project_state(result, version=999) # Use a final version number

async def main(args):
    """Main entry point with resilient execution."""
    initialize_system() # Ensure default configs exist
    
    try:
        async with ZeroToShipOrchestrator() as orchestrator:
            await orchestrator.run_project(args.idea, args.workflow)
    except Exception as e:
        logger.error(f"Orchestrator failed: {e}. Running in registry-less fallback mode.")
        # This is the simplified fallback from your original script
        project_data = {
            "idea": args.idea,
            "workflow": args.workflow,
            "state": "TASK_EXECUTION",  # Default starting state
            "id": f"fallback_{uuid.uuid4().hex[:8]}"
        }

        # Initialize crews for fallback mode
        try:
            logger.info("Initializing crews for fallback mode...")
            builder = BuilderCrew(project_data)
            validator = ValidatorCrew(project_data)
            marketing = MarketingCrew(project_data)
            launch = LaunchCrew(project_data)
            feedback = FeedbackCrew(project_data)

            # Create the Router Map
            crew_router = CrewRouter({
                "IDEA_VALIDATION": validator,
                "TASK_EXECUTION": builder,
                "MARKETING_PREPARATION": marketing,
                "VALIDATION": validator,
                "LAUNCH": launch,
                "FEEDBACK_COLLECTION": feedback,
                "IN_PROGRESS": builder,
            })

            metrics_dict = {
                "workflow_total": WORKFLOW_TOTAL,
                "workflow_state": WORKFLOW_STATE,
                "workflow_duration_seconds": WORKFLOW_DURATION_SECONDS,
            }

            engine = WorkflowEngine(
                project_data=project_data,
                crew_router=crew_router,
                metrics=metrics_dict
            )
            await engine.run()
        except Exception as fallback_error:
            logger.error(f"Fallback mode also failed: {fallback_error}")
            logger.info("Running in minimal mode without crews...")
            metrics_dict = {
                "workflow_total": WORKFLOW_TOTAL,
                "workflow_state": WORKFLOW_STATE,
                "workflow_duration_seconds": WORKFLOW_DURATION_SECONDS,
            }
            engine = WorkflowEngine(project_data, metrics=metrics_dict)
            await engine.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the ZeroToShip AI Product Studio.")
    parser.add_argument("--idea", type=str, required=True, help="The project idea to process.")
    parser.add_argument("--workflow", type=str, required=True, help="The name of the workflow to execute.")
    
    args = parser.parse_args()
    asyncio.run(main(args))