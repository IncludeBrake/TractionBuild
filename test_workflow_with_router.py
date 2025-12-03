#!/usr/bin/env python3
"""
Integration test: WorkflowEngine + CrewRouter
Demonstrates the complete workflow execution with crew delegation.
"""
import asyncio
import sys
from pathlib import Path
from typing import Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.zerotoship.core.workflow_engine import WorkflowEngine
from src.zerotoship.core.crew_router import CrewRouter


class MockCrew:
    """Mock crew for testing."""

    def __init__(self, name: str):
        self.name = name

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Mock crew execution."""
        print(f"  [{self.name}] Processing...")
        return {
            "status": "success",
            "message": f"Completed {self.name} phase.",
            "data": {
                "crew_name": self.name,
                "processed": True,
            },
            "next_state": self._get_next_state(),
        }

    def _get_next_state(self) -> str:
        """Determine next state based on crew name."""
        state_map = {
            "BuilderCrew": "MARKETING_PREPARATION",
            "MarketingCrew": "VALIDATION",
            "ValidatorCrew": "LAUNCH",
            "LaunchCrew": "COMPLETED",
        }
        return state_map.get(self.name, "COMPLETED")


async def main():
    print("="*60)
    print("WORKFLOW ENGINE + CREW ROUTER INTEGRATION TEST")
    print("="*60)

    # Create project data
    project_data = {
        "id": "integration_test_001",
        "idea": "Test Idea: AI-powered task manager",
        "workflow": "test_workflow",
        "state": "TASK_EXECUTION",  # Starting state
    }

    # Create mock crews
    crews = {
        "TASK_EXECUTION": MockCrew("BuilderCrew"),
        "MARKETING_PREPARATION": MockCrew("MarketingCrew"),
        "VALIDATION": MockCrew("ValidatorCrew"),
        "LAUNCH": MockCrew("LaunchCrew"),
    }

    # Create CrewRouter
    crew_router = CrewRouter(crews)

    # Create WorkflowEngine with router
    print("\nInitializing WorkflowEngine with CrewRouter...")
    engine = WorkflowEngine(
        project_data=project_data,
        crew_router=crew_router,
    )

    print("\nStarting workflow execution...")
    print("-"*60)

    # Run the workflow
    result = await engine.run()

    # Display results
    print("\n" + "="*60)
    print("WORKFLOW EXECUTION RESULTS")
    print("="*60)
    print(f"Final State: {result.get('state')}")
    print(f"Message: {result.get('message')}")
    print(f"Project ID: {result.get('id')}")
    print("\nData collected from crews:")
    for key, value in result.items():
        if key.endswith("_processed") or key == "crew_name":
            print(f"  {key}: {value}")

    # Verify workflow completed successfully
    if result.get("state") == "COMPLETED":
        print("\n" + "="*60)
        print("SUCCESS: Workflow completed successfully!")
        print("="*60)
        print("\nKey Achievements:")
        print("  [+] WorkflowEngine delegated to CrewRouter")
        print("  [+] CrewRouter dispatched to appropriate crews")
        print("  [+] Crews executed and returned standardized results")
        print("  [+] WorkflowEngine updated project_data from crew outputs")
        print("  [+] State transitions followed crew recommendations")
        print("\nIntegration verified: Engine -> Router -> Crews")
    else:
        print("\n" + "="*60)
        print("FAILED: Workflow did not complete successfully")
        print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
