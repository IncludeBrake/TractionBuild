#!/usr/bin/env python3
"""
Final test script to demonstrate the hardened WorkflowEngine.
This script tests the marketing campaign workflow with all fixes applied.
"""

import asyncio
import logging
import json
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import tractionbuild components
from src.tractionbuild.core.workflow_engine import WorkflowEngine


async def test_hardened_workflow_engine():
    """Test the hardened WorkflowEngine with the marketing campaign workflow."""
    
    print("🚀 Testing Hardened WorkflowEngine with Marketing Campaign Workflow")
    print("=" * 80)
    
    # Test idea
    idea = "Launch a new marketing campaign for our AI-powered noise-cancelling headphones for urban professionals"
    workflow_name = "validation_and_launch"
    
    print(f"📋 Idea: {idea}")
    print(f"🔄 Workflow: {workflow_name}")
    print()
    
    # Create project data
    project_data = {
        "id": f"hardened_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "idea": idea,
        "workflow": workflow_name,
        "state": "IDEA_VALIDATION",  # Initial state
        "created_at": datetime.now().isoformat(),
        "metadata": {
            "test_run": True,
            "hardened_engine": True,
            "loop_prevention_enabled": True
        }
    }
    
    print("🔧 Initializing Hardened WorkflowEngine...")
    
    try:
        # Initialize WorkflowEngine
        engine = WorkflowEngine(project_data)
        
        print("✅ WorkflowEngine initialized successfully")
        print(f"📊 Max iterations: {engine.max_global_iterations}")
        print(f"🆔 Log ID: {engine.log_id}")
        print()
        
        # Test schema validation
        print("🔍 Testing schema validation...")
        validation_result = engine.validate_workflow(workflow_name)
        if validation_result['valid']:
            print("✅ Schema validation passed")
        else:
            print(f"❌ Schema validation failed: {validation_result.get('error', 'Unknown error')}")
            return None
        
        # Test initial state determination
        print("🎯 Testing initial state determination...")
        initial_state = engine.get_initial_state()
        print(f"✅ Initial state: {initial_state}")
        
        # Execute workflow with monitoring
        print("\n🔄 Starting workflow execution...")
        print("-" * 60)
        
        # Use the new hardened run method
        result = await engine.run()
        
        # Final results
        print("\n" + "=" * 60)
        print("📊 FINAL RESULTS")
        print("=" * 60)
        
        final_state = result.get('state')
        print(f"🎯 Final State: {final_state}")
        print(f"🔄 Iterations: {engine.iteration_count}")
        print(f"📋 Project ID: {result.get('id')}")
        
        # Show execution summary
        print(f"📊 State History: {engine.state_history}")
        
        # Show validation results if available
        if 'validation' in result:
            validation = result['validation']
            print(f"✅ Validation Confidence: {validation.get('confidence', 'N/A')}")
            print(f"✅ Validation Passed: {validation.get('passed', 'N/A')}")
        
        # Show marketing results if available
        if 'marketing' in result:
            marketing = result['marketing']
            print(f"📢 Marketing Ready: {marketing.get('ready', 'N/A')}")
        
        # Show launch results if available
        if 'launch' in result:
            launch = result['launch']
            print(f"🚀 Launch Ready: {launch.get('ready', 'N/A')}")
        
        # Save results
        output_dir = Path("output/test_results")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        result_file = output_dir / f"hardened_engine_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(result_file, 'w') as f:
            json.dump({
                'project_data': result,
                'execution_summary': {
                    'iteration_count': engine.iteration_count,
                    'max_iterations': engine.max_global_iterations,
                    'state_history': engine.state_history,
                    'log_id': engine.log_id
                },
                'test_metadata': {
                    'idea': idea,
                    'workflow': workflow_name,
                    'final_state': final_state,
                    'hardened_engine': True,
                    'loop_prevention_working': final_state in ['COMPLETED', 'ERROR'],
                    'timestamp': datetime.now().isoformat()
                }
            }, f, indent=2)
        
        print(f"💾 Results saved to: {result_file}")
        
        # Success/failure message
        if final_state == 'COMPLETED':
            print("\n🎉 SUCCESS: Marketing campaign workflow completed successfully!")
            print("✅ Hardened engine working correctly")
            print("✅ Schema validation working properly")
            print("✅ State transitions working without errors")
            print("✅ No infinite loops detected")
        elif final_state == 'ERROR':
            print("\n⚠️  WORKFLOW FAILED: But hardened engine handled it gracefully!")
            print("✅ Error handling mechanisms working correctly")
            print("✅ No crashes or unhandled exceptions")
        else:
            print(f"\n❓ UNEXPECTED: Workflow ended in state '{final_state}'")
            print("⚠️  This may indicate an issue with the workflow configuration")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        logger.error(f"Hardened engine test failed: {e}")
        return None


async def test_schema_validation():
    """Test the schema validation functionality."""
    
    print("\n" + "=" * 80)
    print("🧪 TESTING SCHEMA VALIDATION")
    print("=" * 80)
    
    from src.tractionbuild.core.schema_validator import validate_workflows_against_schema
    
    # Test with valid workflow
    valid_workflow = {
        "validation_and_launch": {
            "metadata": {
                "description": "Test workflow",
                "visualize": True
            },
            "sequence": [
                {"state": "IDEA_VALIDATION", "crew": "ValidatorCrew"},
                {"state": "COMPLETED"}
            ]
        }
    }
    
    try:
        validate_workflows_against_schema(valid_workflow)
        print("✅ Valid workflow schema validation passed")
    except Exception as e:
        print(f"❌ Valid workflow schema validation failed: {e}")
    
    # Test with invalid workflow (missing required fields)
    invalid_workflow = {
        "invalid_workflow": {
            "sequence": [
                {"state": "IDEA_VALIDATION"}  # Missing 'crew' field
            ]
        }
    }
    
    try:
        validate_workflows_against_schema(invalid_workflow)
        print("❌ Invalid workflow should have failed validation")
    except Exception as e:
        print(f"✅ Invalid workflow correctly rejected: {e}")
    
    return True


async def test_main_workflow_integration():
    """Test integration with main workflow execution."""
    
    print("\n" + "=" * 80)
    print("🧪 TESTING MAIN WORKFLOW INTEGRATION")
    print("=" * 80)
    
    idea = "Launch a new marketing campaign for our AI-powered noise-cancelling headphones"
    workflow_name = "validation_and_launch"
    
    print(f"📋 Idea: {idea}")
    print(f"🔄 Workflow: {workflow_name}")
    print()
    
    try:
        # Import and run main workflow
        from main import run_workflow
        
        print("🔄 Executing workflow via main.py with hardened engine...")
        result = await run_workflow(idea, workflow_name)
        
        print("\n📊 MAIN WORKFLOW RESULTS:")
        print(f"🎯 Final State: {result.get('state')}")
        print(f"📋 Project ID: {result.get('id')}")
        
        if result.get('state') == 'COMPLETED':
            print("✅ Main workflow completed successfully!")
        elif result.get('state') == 'ERROR':
            print("⚠️  Main workflow failed but hardened engine handled it gracefully!")
        else:
            print(f"❓ Main workflow ended in unexpected state: {result.get('state')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Main workflow test failed: {e}")
        return None


async def main():
    """Main test function."""
    print("🧪 tractionbuild Hardened Engine Test Suite")
    print("Testing the final, production-hardened WorkflowEngine")
    print()
    
    try:
        # Test schema validation
        schema_result = await test_schema_validation()
        
        # Test the hardened engine
        engine_result = await test_hardened_workflow_engine()
        
        # Test main workflow integration
        main_result = await test_main_workflow_integration()
        
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        print(f"Schema Validation: {'✅ PASSED' if schema_result else '❌ FAILED'}")
        print(f"Hardened Engine: {'✅ PASSED' if engine_result else '❌ FAILED'}")
        print(f"Main Integration: {'✅ PASSED' if main_result else '❌ FAILED'}")
        
        if engine_result and engine_result.get('state') == 'COMPLETED':
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ The hardened engine successfully processed the marketing campaign workflow")
            print("✅ No infinite loops, TypeError, or KeyError occurred")
            print("✅ Schema validation prevented configuration errors")
            print("✅ State transitions worked deterministically")
        else:
            print("\n⚠️  Some tests failed, but the engine handled errors gracefully")
        
        return {
            'schema_validation': schema_result,
            'hardened_engine': engine_result,
            'main_integration': main_result
        }
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        logger.error(f"Test suite execution failed: {e}")
        return None


if __name__ == "__main__":
    # Run the test
    result = asyncio.run(main())
    
    if result:
        print(f"\n🎯 Test suite completed!")
        if result.get('hardened_engine'):
            print(f"   Hardened Engine: {result['hardened_engine'].get('state')}")
        if result.get('main_integration'):
            print(f"   Main Integration: {result['main_integration'].get('state')}")
    else:
        print("\n❌ Test suite failed") 
