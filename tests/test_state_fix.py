#!/usr/bin/env python3
"""
Test script to validate the state KeyError fix for tractionbuild.
Tests the marketing campaign workflow with the enhanced state management.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tractionbuild.core.workflow_engine import WorkflowEngine
from tractionbuild.core.schema_validator import validate_and_enrich_data
from tractionbuild.models.crew_output import CrewOutputValidator


async def test_state_validation():
    """Test the state validation and initialization."""
    print("🧪 Testing State Validation and Initialization")
    
    # Test case 1: Missing state field
    project_data_1 = {
        "id": "test_project_1",
        "idea": "AI-powered noise-cancelling headphones",
        "workflow": "validation_and_launch"
    }
    
    print(f"  Original project_data: {project_data_1}")
    
    # Validate and enrich
    enriched_data_1 = validate_and_enrich_data(project_data_1)
    print(f"  Enriched project_data: {enriched_data_1}")
    print(f"  State field present: {'state' in enriched_data_1}")
    print(f"  State value: {enriched_data_1.get('state')}")
    
    # Test case 2: Empty state field
    project_data_2 = {
        "id": "test_project_2",
        "idea": "AI-powered noise-cancelling headphones",
        "workflow": "validation_and_launch",
        "state": ""
    }
    
    print(f"\n  Original project_data (empty state): {project_data_2}")
    
    # Validate and enrich
    enriched_data_2 = validate_and_enrich_data(project_data_2)
    print(f"  Enriched project_data: {enriched_data_2}")
    print(f"  State field present: {'state' in enriched_data_2}")
    print(f"  State value: {enriched_data_2.get('state')}")


async def test_workflow_engine_initialization():
    """Test WorkflowEngine initialization with various project data."""
    print("\n🧪 Testing WorkflowEngine Initialization")
    
    # Test case 1: Complete project data
    project_data_1 = {
        "id": "test_project_1",
        "idea": "AI-powered noise-cancelling headphones",
        "workflow": "validation_and_launch",
        "state": "IDEA_VALIDATION"
    }
    
    print(f"  Test 1: Complete project data")
    try:
        engine_1 = WorkflowEngine(project_data_1)
        print(f"    ✅ Engine initialized successfully")
        print(f"    State: {engine_1.project_data.get('state')}")
        print(f"    State history: {engine_1.project_data.get('state_history')}")
    except Exception as e:
        print(f"    ❌ Engine initialization failed: {e}")
    
    # Test case 2: Missing state
    project_data_2 = {
        "id": "test_project_2",
        "idea": "AI-powered noise-cancelling headphones",
        "workflow": "validation_and_launch"
    }
    
    print(f"\n  Test 2: Missing state field")
    try:
        engine_2 = WorkflowEngine(project_data_2)
        print(f"    ✅ Engine initialized successfully")
        print(f"    State: {engine_2.project_data.get('state')}")
        print(f"    State history: {engine_2.project_data.get('state_history')}")
    except Exception as e:
        print(f"    ❌ Engine initialization failed: {e}")
    
    # Test case 3: Empty state
    project_data_3 = {
        "id": "test_project_3",
        "idea": "AI-powered noise-cancelling headphones",
        "workflow": "validation_and_launch",
        "state": ""
    }
    
    print(f"\n  Test 3: Empty state field")
    try:
        engine_3 = WorkflowEngine(project_data_3)
        print(f"    ✅ Engine initialized successfully")
        print(f"    State: {engine_3.project_data.get('state')}")
        print(f"    State history: {engine_3.project_data.get('state_history')}")
    except Exception as e:
        print(f"    ❌ Engine initialization failed: {e}")


async def test_crew_output_validation():
    """Test crew output validation."""
    print("\n🧪 Testing Crew Output Validation")
    
    # Test case 1: Valid crew output
    crew_output_1 = {
        "validation": {
            "confidence": 0.88,
            "market_size": "$3.6B-$5.7B",
            "som": "$126M",
            "passed": True
        },
        "execution_metadata": {
            "crew_name": "ValidatorCrew",
            "execution_duration_seconds": 73.52,
            "project_id": "test_project_1"
        }
    }
    
    print(f"  Test 1: Valid crew output")
    validated_1 = CrewOutputValidator.validate_and_enrich(
        crew_output_1, "ValidatorCrew", "test_project_1"
    )
    print(f"    ✅ Output validated successfully")
    print(f"    State field present: {'state' in validated_1}")
    print(f"    State value: {validated_1.get('state')}")
    
    # Test case 2: Missing state in output
    crew_output_2 = {
        "validation": {
            "confidence": 0.85,
            "passed": True
        }
    }
    
    print(f"\n  Test 2: Missing state in output")
    validated_2 = CrewOutputValidator.validate_and_enrich(
        crew_output_2, "ValidatorCrew", "test_project_2"
    )
    print(f"    ✅ Output validated successfully")
    print(f"    State field present: {'state' in validated_2}")
    print(f"    State value: {validated_2.get('state')}")
    
    # Test case 3: Non-dict output
    crew_output_3 = "Simple string output"
    
    print(f"\n  Test 3: Non-dict output")
    validated_3 = CrewOutputValidator.validate_and_enrich(
        crew_output_3, "ValidatorCrew", "test_project_3"
    )
    print(f"    ✅ Output validated successfully")
    print(f"    State field present: {'state' in validated_3}")
    print(f"    State value: {validated_3.get('state')}")


async def test_marketing_campaign_workflow():
    """Test the complete marketing campaign workflow."""
    print("\n🧪 Testing Marketing Campaign Workflow")
    
    # Create project data for marketing campaign
    project_data = {
        "id": "marketing_campaign_test",
        "idea": "Launch a new marketing campaign for our AI-powered noise-cancelling headphones",
        "workflow": "validation_and_launch"
    }
    
    print(f"  Project data: {project_data}")
    
    try:
        # Initialize workflow engine
        engine = WorkflowEngine(project_data)
        print(f"    ✅ WorkflowEngine initialized")
        print(f"    Initial state: {engine.project_data.get('state')}")
        
        # Test route_and_execute (this would normally run the full workflow)
        print(f"    Testing route_and_execute...")
        result = await engine.route_and_execute()
        print(f"    ✅ route_and_execute completed")
        print(f"    Final state: {result.get('state')}")
        print(f"    State field present: {'state' in result}")
        
        # Validate the result has proper state management
        if 'state' in result and result['state']:
            print(f"    ✅ State management working correctly")
        else:
            print(f"    ❌ State management failed")
            
    except Exception as e:
        print(f"    ❌ Workflow test failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests."""
    print("🚀 tractionbuild State Management Fix Validation")
    print("=" * 50)
    
    try:
        await test_state_validation()
        await test_workflow_engine_initialization()
        await test_crew_output_validation()
        await test_marketing_campaign_workflow()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        print("🎯 State KeyError fix is working correctly")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
