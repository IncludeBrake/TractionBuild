import asyncio
import logging
from src.zerotoship.core.workflow_engine import WorkflowEngine
from src.zerotoship.core.crew_router import CrewRouter

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
    def __init__(self, name, next_state_suggestion):
        self.name = name
        self.next_state = next_state_suggestion

    async def run(self, context: dict) -> dict:
        logger.info(f"[{self.name}] Received task. Context keys: {list(context.keys())}")

        # Simulate 'work'
        await asyncio.sleep(0.5)

        return {
            "status": "success",
            "message": f"[SUCCESS] {self.name} completed its phase.",
            "data": {f"{self.name.lower()}_output": "Simulated Data"},
            "next_state": self.next_state
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
    builder = MockCrew("BuilderCrew", "MARKETING_PREPARATION")
    marketing = MockCrew("MarketingCrew", "VALIDATION")
    validator = MockCrew("ValidatorCrew", "LAUNCH")
    launch = MockCrew("LaunchCrew", "COMPLETED")

    # C. Setup Router (The "Nervous System")
    # This proves the Router can handle ANY object that has a run() method

    crew_router = CrewRouter({
        "TASK_EXECUTION": builder,
        "MARKETING_PREPARATION": marketing,
        "VALIDATION": validator,
        "LAUNCH": launch,
    })

    # D. Setup Engine (The "Brain")
    # We inject the router, verifying Block 3
    engine = WorkflowEngine(
        project_data=project_data,
        crew_router=crew_router
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
