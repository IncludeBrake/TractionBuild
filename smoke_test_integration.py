import asyncio
import logging
from src.zerotoship.core.workflow_engine import WorkflowEngine
from src.zerotoship.core.crew_router import CrewRouter
from src.zerotoship.core.context_bus import ContextBus # Import ContextBus

# Configure logging to see the flow clearly
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("SmokeTest")

# --- 1. Define a Generic Mock Crew ---
class MockCrew:
    """
    A fake crew that adheres to the Block 1 Interface.
    It simulates work without needing external dependencies.
    """
    def __init__(self, project_data: dict):
        self.name = project_data.get("state") + "Crew"
        self.next_state = "COMPLETED" # Default next state
        self.project_data = project_data

    async def run(self, context: dict) -> dict:
        logger.info(f"[{self.name}] Received task. Context keys: {list(context.keys())}")

        # Simulate 'work'
        await asyncio.sleep(0.5)

        # The next state should come from the context or be determined by the crew itself
        # For this mock, we'll use a simple sequential flow
        next_state_map = {
            "TASK_EXECUTION": "MARKETING_PREPARATION",
            "MARKETING_PREPARATION": "VALIDATION",
            "VALIDATION": "LAUNCH",
            "LAUNCH": "COMPLETED",
            "IN_PROGRESS": "COMPLETED"
        }
        next_state = next_state_map.get(self.project_data.get("state"), "COMPLETED")


        return {
            "status": "success",
            "message": f"[SUCCESS] {self.name} completed its phase.",
            "data": {f"{self.name.lower()}_output": "Simulated Data"},
            "next_state": next_state
        }

# --- 2. The Integration Test ---
async def run_smoke_test():
    print("\n" + "="*50)
    print("STARTING ARCHITECTURE SMOKE TEST")
    print("="*50 + "\n")

    # A. Setup Project Data
    project_data = {
        "idea": "Smoke Test App",
        "state": "TASK_EXECUTION" # Starting Point
    }

    # B. Instantiate Mocks (The "Muscles")
    # We wire them up to point to the next logical state
    # Now we pass crew classes, not instances
    crew_router = CrewRouter({
        "TASK_EXECUTION": MockCrew,
        "MARKETING_PREPARATION": MockCrew,
        "VALIDATION": MockCrew,
        "LAUNCH": MockCrew,
    }, context_bus=ContextBus()) # Pass context_bus to CrewRouter

    # D. Setup Engine (The "Brain")
    # We inject the router, verifying Block 3
    engine = WorkflowEngine(
        project_data=project_data,
        crew_router=crew_router,
        context_bus=crew_router.context_bus # Pass the same context_bus
    )

    # E. Run!
    try:
        await engine.run()
        print("\n" + "="*50)
        print("[SUCCESS] SMOKE TEST PASSED: End-to-End Flow Successful")
        print("="*50)
    except Exception as e:
        print(f"\n[FAILED] SMOKE TEST FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(run_smoke_test())
