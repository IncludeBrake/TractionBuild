#!/usr/bin/env python3
"""
Test script to verify CrewRouter dispatches crews correctly.
Tests routing, error handling, and integration with standardized crew interface.
"""
import asyncio
import sys
from pathlib import Path
from typing import Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.zerotoship.core.crew_router import CrewRouter


class MockCrew:
    """Mock crew for testing the router."""

    def __init__(self, name: str, should_fail: bool = False):
        self.name = name
        self.should_fail = should_fail

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Mock run method following standardized interface."""
        print(f"  > MockCrew '{self.name}' executing with context: {context}")

        if self.should_fail:
            raise RuntimeError(f"Mock failure in {self.name}")

        return {
            "status": "success",
            "message": f"Completed {self.name} phase.",
            "data": {
                "crew_name": self.name,
                "context_received": context,
            },
            "next_state": "NEXT_STATE",
        }


async def test_successful_execution():
    """Test successful crew execution through router."""
    print("\n" + "="*60)
    print("TEST 1: Successful Crew Execution")
    print("="*60)

    # Create mock crews
    crews = {
        "TASK_EXECUTION": MockCrew("BuilderCrew"),
        "MARKETING_PREPARATION": MockCrew("MarketingCrew"),
        "VALIDATION": MockCrew("ValidatorCrew"),
    }

    # Create router
    router = CrewRouter(crews)

    # Execute a crew
    context = {"idea": "Test Idea", "test_mode": True}
    result = await router.execute("TASK_EXECUTION", context)

    # Verify result
    print(f"\nResult:")
    print(f"  Status: {result['status']}")
    print(f"  Message: {result['message']}")
    print(f"  Data: {result.get('data', {})}")

    assert result["status"] == "success", "Expected success status"
    assert "BuilderCrew" in result["message"], "Expected BuilderCrew in message"

    print("\n[PASS] Test 1 PASSED")
    return True


async def test_missing_crew():
    """Test handling of missing crew for a state."""
    print("\n" + "="*60)
    print("TEST 2: Missing Crew Handling")
    print("="*60)

    crews = {
        "TASK_EXECUTION": MockCrew("BuilderCrew"),
    }

    router = CrewRouter(crews)

    # Try to execute a state with no crew
    context = {"idea": "Test Idea"}
    result = await router.execute("UNKNOWN_STATE", context)

    print(f"\nResult:")
    print(f"  Status: {result['status']}")
    print(f"  Message: {result['message']}")

    assert result["status"] == "skipped", "Expected skipped status"
    assert "No crew for" in result["message"], "Expected no crew message"

    print("\n[PASS] Test 2 PASSED")
    return True


async def test_crew_failure():
    """Test handling of crew execution failure."""
    print("\n" + "="*60)
    print("TEST 3: Crew Execution Failure")
    print("="*60)

    crews = {
        "TASK_EXECUTION": MockCrew("FailingCrew", should_fail=True),
    }

    router = CrewRouter(crews)

    # Execute a failing crew
    context = {"idea": "Test Idea"}
    result = await router.execute("TASK_EXECUTION", context)

    print(f"\nResult:")
    print(f"  Status: {result['status']}")
    print(f"  Message: {result['message']}")
    print(f"  Error Type: {result.get('error_type', 'N/A')}")

    assert result["status"] == "error", "Expected error status"
    assert "Mock failure" in result["message"], "Expected error message"
    assert result.get("error_type") == "RuntimeError", "Expected RuntimeError type"

    print("\n[PASS] Test 3 PASSED")
    return True


async def test_multiple_sequential_executions():
    """Test executing multiple crews sequentially."""
    print("\n" + "="*60)
    print("TEST 4: Sequential Crew Executions")
    print("="*60)

    crews = {
        "TASK_EXECUTION": MockCrew("BuilderCrew"),
        "MARKETING_PREPARATION": MockCrew("MarketingCrew"),
        "VALIDATION": MockCrew("ValidatorCrew"),
        "LAUNCH": MockCrew("LaunchCrew"),
    }

    router = CrewRouter(crews)

    # Execute multiple states in sequence
    states = ["TASK_EXECUTION", "MARKETING_PREPARATION", "VALIDATION", "LAUNCH"]
    context = {"idea": "Sequential Test"}

    results = []
    for state in states:
        print(f"\nExecuting: {state}")
        result = await router.execute(state, context)
        results.append((state, result))

    # Verify all succeeded
    print("\n" + "-"*60)
    print("Results Summary:")
    for state, result in results:
        status = result["status"]
        print(f"  {state}: {status}")
        assert result["status"] == "success", f"Expected success for {state}"

    print("\n[PASS] Test 4 PASSED")
    return True


async def main():
    """Run all tests."""
    print("="*60)
    print("CREW ROUTER TEST SUITE")
    print("="*60)

    tests = [
        test_successful_execution,
        test_missing_crew,
        test_crew_failure,
        test_multiple_sequential_executions,
    ]

    results = []
    for test in tests:
        try:
            success = await test()
            results.append((test.__name__, success))
        except Exception as e:
            print(f"\n[FAIL] Test {test.__name__} FAILED: {e}")
            results.append((test.__name__, False))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        symbol = "[+]" if success else "[-]"
        print(f"  {symbol} {test_name}: {status}")

    total = len(results)
    passed = sum(1 for _, success in results if success)

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n" + "="*60)
        print("SUCCESS: All CrewRouter tests passed!")
        print("="*60)
        print("\nCrewRouter is ready for integration:")
        print("  await crew_router.execute(state, context)")
    else:
        print("\n" + "="*60)
        print("FAILURE: Some tests failed")
        print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
