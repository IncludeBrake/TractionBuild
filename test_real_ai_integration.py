#!/usr/bin/env python3
"""
Test Real AI Integration - Track A.2
Tests the complete workflow with real CrewAI agents.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.zerotoship.core.workflow_engine import WorkflowEngine
from src.zerotoship.core.crew_router import CrewRouter

# Try to import the simple crews
try:
    from src.zerotoship.crews.simple_builder_crew import SimpleBuilderCrew
    from src.zerotoship.crews.simple_marketing_crew import SimpleMarketingCrew
    from src.zerotoship.crews.simple_validator_crew import SimpleValidatorCrew
    from src.zerotoship.crews.simple_launch_crew import SimpleLaunchCrew
    CREWS_AVAILABLE = True
except ImportError as e:
    print(f"Error importing crews: {e}")
    CREWS_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("RealAITest")


async def test_real_ai_workflow():
    """Run the complete workflow with real AI agents."""
    print("\n" + "="*80)
    print("TRACK A.2 - REAL AI INTEGRATION TEST")
    print("="*80 + "\n")

    if not CREWS_AVAILABLE:
        print("[ERROR] Could not import crews. Please check dependencies.")
        return False

    # Check if API key is configured
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[WARNING] OPENAI_API_KEY not set. CrewAI will fail without an LLM API key.")
        print("Set it with: export OPENAI_API_KEY=your-key-here")
        print("\nFor testing purposes, you can:")
        print("1. Get a free OpenAI API key from https://platform.openai.com/")
        print("2. Or use another LLM provider supported by CrewAI")
        return False

    print("Configuration:")
    print(f"  - OpenAI API Key: {'*' * 20}{api_key[-4:]}")
    print()

    # Setup project data
    project_data = {
        "id": "real_ai_test_001",
        "idea": "AI-powered task management app that learns your work patterns and suggests optimal scheduling",
        "workflow": "full_workflow",
        "state": "TASK_EXECUTION"  # Starting state
    }

    print(f"Project ID: {project_data['id']}")
    print(f"Idea: {project_data['idea']}")
    print(f"Initial State: {project_data['state']}")
    print()

    print("="*80)
    print("INITIALIZING REAL AI CREWS")
    print("="*80 + "\n")

    try:
        # Instantiate the real AI crews
        print("[1/4] Creating SimpleBuilderCrew...")
        builder = SimpleBuilderCrew(project_data)

        print("[2/4] Creating SimpleMarketingCrew...")
        marketing = SimpleMarketingCrew(project_data)

        print("[3/4] Creating SimpleValidatorCrew...")
        validator = SimpleValidatorCrew(project_data)

        print("[4/4] Creating SimpleLaunchCrew...")
        launch = SimpleLaunchCrew(project_data)

        print("\n[SUCCESS] All crews instantiated successfully!")

    except Exception as e:
        print(f"\n[ERROR] Failed to instantiate crews: {e}")
        logger.exception("Crew instantiation failed")
        return False

    # Create CrewRouter
    print("\n" + "="*80)
    print("SETTING UP CREW ROUTER")
    print("="*80 + "\n")

    crew_router = CrewRouter({
        "TASK_EXECUTION": builder,
        "MARKETING_PREPARATION": marketing,
        "VALIDATION": validator,
        "LAUNCH": launch,
    })

    print("[SUCCESS] CrewRouter configured with 4 crews")

    # Create WorkflowEngine
    print("\n" + "="*80)
    print("INITIALIZING WORKFLOW ENGINE")
    print("="*80 + "\n")

    engine = WorkflowEngine(
        project_data=project_data,
        crew_router=crew_router
    )

    print("[SUCCESS] WorkflowEngine ready")

    # Run the workflow
    print("\n" + "="*80)
    print("STARTING REAL AI WORKFLOW EXECUTION")
    print("="*80)
    print("\nNOTE: This will make real API calls to OpenAI.")
    print("Each crew will run AI agents that generate actual content.")
    print("This may take several minutes and will consume API credits.")
    print("\n" + "="*80 + "\n")

    try:
        result = await engine.run()

        print("\n" + "="*80)
        print("WORKFLOW EXECUTION COMPLETE")
        print("="*80)
        print(f"\nFinal State: {result.get('state')}")
        print(f"Project ID: {result.get('id')}")

        print("\n" + "-"*80)
        print("CREW OUTPUTS:")
        print("-"*80)

        # Display outputs from each crew
        for key, value in result.items():
            if "_output" in key:
                print(f"\n[{key.upper()}]")
                print("-" * 40)
                # Truncate long outputs for readability
                output_str = str(value)
                if len(output_str) > 500:
                    print(output_str[:500] + "...\n[Output truncated]")
                else:
                    print(output_str)

        # Verify success
        print("\n" + "="*80)
        if result.get("state") == "COMPLETED":
            print("SUCCESS: Track A.2 Complete!")
            print("="*80)
            print("\nReal AI Integration Verified:")
            print("  [+] CrewAI agents executed successfully")
            print("  [+] Workflow engine coordinated all crews")
            print("  [+] Each crew generated AI-powered outputs")
            print("  [+] State transitions worked correctly")
            print("  [+] Complete workflow reached COMPLETED state")
            print("\nThe system is now running with real autonomous AI agents!")
            return True
        else:
            print(f"INCOMPLETE: Workflow ended in state: {result.get('state')}")
            print("="*80)
            return False

    except Exception as e:
        print("\n" + "="*80)
        print("WORKFLOW EXECUTION FAILED")
        print("="*80)
        print(f"\nError: {e}")
        logger.exception("Workflow execution failed")
        return False


if __name__ == "__main__":
    print("\nInitializing real AI integration test...\n")
    success = asyncio.run(test_real_ai_workflow())
    sys.exit(0 if success else 1)
