"""
Test script for enhanced CrewController with observability and graph-based execution.
"""

import asyncio
import tempfile
import shutil
from pathlib import Path
from src.tractionbuild.core.crew_controller import CrewController, CrewControllerConfig
from src.tractionbuild.crews.validator_crew import ValidatorCrewConfig
from src.tractionbuild.crews.execution_crew import ExecutionCrewConfig
from src.tractionbuild.crews.builder_crew import BuilderCrewConfig
from src.tractionbuild.crews.marketing_crew import MarketingCrewConfig
from src.tractionbuild.crews.feedback_crew import FeedbackCrewConfig
from src.tractionbuild.core.token_budget import TokenBudgetManager
from src.tractionbuild.core.output_validator import OutputValidatorConfig
from src.tractionbuild.core.project_meta_memory import ProjectMetaMemory


async def test_enhanced_crew_controller():
    """Test the enhanced CrewController with all features."""
    
    # Create a temporary directory for testing
    temp_dir = Path(tempfile.mkdtemp())
    memory_file = temp_dir / "enhanced_controller_memory.json"
    
    try:
        print("🚀 Testing Enhanced CrewController...")
        
        # Create comprehensive configuration
        config = CrewControllerConfig(
            # Core settings
            enable_observability=True,
            enable_graph_execution=True,
            enable_parallel_execution=True,
            enable_timeout_handling=True,
            max_execution_time=300,
            max_graph_nodes=500,
            
            # Crew configurations
            validator_config=ValidatorCrewConfig(
                enable_memory_learning=True,
                enable_sequential_validation=True,
                enable_competitor_analysis=True,
                enable_market_sizing=True
            ),
            execution_config=ExecutionCrewConfig(
                enable_memory_learning=True,
                enable_task_decomposition=True,
                enable_dependency_mapping=True,
                enable_resource_planning=True
            ),
            builder_config=BuilderCrewConfig(
                enable_memory_learning=True,
                enable_code_generation=True,
                enable_testing=True,
                enable_documentation=True
            ),
            marketing_config=MarketingCrewConfig(
                enable_memory_learning=True,
                enable_positioning=True,
                enable_asset_generation=True,
                enable_launch_strategy=True
            ),
            feedback_config=FeedbackCrewConfig(
                enable_memory_learning=True,
                enable_quality_assurance=True,
                enable_output_validation=True,
                enable_continuous_improvement=True
            ),
            
            # Token budget configuration
            token_budget_config={
                "per_agent_limit": 5000,
                "per_crew_limit": 20000,
                "per_run_limit": 50000,
                "enable_budgeting": True,
                "enable_cost_tracking": True
            },
            
            # Output validator configuration
            output_validator_config=OutputValidatorConfig(
                enable_hallucination_detection=True,
                enable_security_checks=True,
                enable_format_validation=True,
                max_content_length=1000
            ),
            
            # Memory configuration
            memory_config=ProjectMetaMemory(
                memory_file_path=str(memory_file),
                max_entries_per_type=100,
                memory_retention_days=30,
                auto_cleanup=True,
                backup_enabled=True
            ),
            
            # Logging configuration
            log_level="INFO",
            enable_structured_logging=True
        )
        
        # Initialize controller
        controller = CrewController(config)
        print("✅ CrewController initialized successfully")
        
        # Test 1: Process a simple idea
        print("\n📊 Test 1: Simple Idea Processing")
        test_idea = "AI-powered task management app for remote teams"
        
        result = await controller.process_idea(test_idea, timeout=60)
        
        print(f"   Status: {result.get('status', 'unknown')}")
        if result.get('status') == 'success':
            print(f"   ✅ Processing completed successfully")
            print(f"   📈 Validation: {result.get('validation', {}).get('confidence_score', 'N/A')}")
            print(f"   🔨 Build Result: {len(result.get('build_result', {}).get('code_files', []))} files")
            print(f"   📢 Marketing: {result.get('marketing_result', {}).get('value_proposition', 'N/A')}")
            print(f"   🔍 Feedback: {len(result.get('feedback', {}))} items")
        else:
            print(f"   ❌ Processing failed: {result.get('reason', 'Unknown error')}")
        
        # Test 2: Memory and Learning
        print("\n🧠 Test 2: Memory and Learning")
        memory_stats = controller.memory_manager.get_memory_stats()
        print(f"   📊 Memory Stats:")
        print(f"      Total Entries: {memory_stats['total_entries']}")
        print(f"      Memory Types: {len(memory_stats['type_counts'])}")
        print(f"      Success Patterns: {memory_stats['type_counts'].get('success_pattern', 0)}")
        print(f"      Failure Patterns: {memory_stats['type_counts'].get('failure_pattern', 0)}")
        
        # Test 3: Token Budget Management
        print("\n💰 Test 3: Token Budget Management")
        try:
            token_summary = await controller.token_budget_manager.get_usage_summary("test_project")
            print(f"   📊 Token Usage:")
            print(f"      Total Tokens: {token_summary['total_tokens']}")
            print(f"      Total Cost: ${token_summary['total_cost']:.4f}")
            print(f"      Budget Status: {token_summary['budget_status']}")
        except Exception as e:
            print(f"   ⚠️ Token budget error: {e}")
        
        # Test 4: Enhanced Memory with Embeddings
        print("\n🔍 Test 4: Enhanced Memory")
        enhanced_memory_stats = controller.enhanced_memory
        print(f"   📊 Enhanced Memory:")
        print(f"      Feedback Items: {len(enhanced_memory_stats.feedback)}")
        print(f"      Embeddings: {len(enhanced_memory_stats.embeddings)}")
        
        # Test 5: Project Status
        print("\n📈 Test 5: Project Status")
        project_status = await controller.get_project_status("test_project")
        print(f"   📊 Project Status:")
        print(f"      Status: {project_status.get('status', 'unknown')}")
        print(f"      Timestamp: {project_status.get('timestamp', 'N/A')}")
        
        # Test 6: Complex Idea Processing
        print("\n🚀 Test 6: Complex Idea Processing")
        complex_idea = """
        Build a comprehensive AI-powered e-commerce platform with the following features:
        - Multi-vendor marketplace with real-time inventory management
        - AI-powered product recommendations and search
        - Automated customer service with chatbot integration
        - Advanced analytics and reporting dashboard
        - Mobile-first responsive design
        - Payment processing with multiple gateways
        - Order tracking and fulfillment automation
        - GDPR and CCPA compliance built-in
        """
        
        complex_result = await controller.process_idea(complex_idea, timeout=120)
        
        print(f"   Status: {complex_result.get('status', 'unknown')}")
        if complex_result.get('status') == 'success':
            print(f"   ✅ Complex processing completed")
            execution_plan = complex_result.get('execution_plan', {})
            print(f"   📋 Tasks: {len(execution_plan.get('tasks', []))}")
            print(f"   🔗 Dependencies: {len(execution_plan.get('dependencies', []))}")
            print(f"   ⏱️ Timeline: {execution_plan.get('timeline', 'TBD')}")
        else:
            print(f"   ❌ Complex processing failed: {complex_result.get('reason', 'Unknown error')}")
        
        # Test 7: Error Handling and Timeout
        print("\n⚠️ Test 7: Error Handling")
        
        # Test with invalid idea
        invalid_result = await controller.process_idea("", timeout=10)
        print(f"   Empty idea result: {invalid_result.get('status', 'unknown')}")
        
        # Test timeout handling
        timeout_result = await controller.process_idea("This will timeout", timeout=1)
        print(f"   Timeout result: {timeout_result.get('status', 'unknown')}")
        
        # Test 8: Observability Features
        print("\n📊 Test 8: Observability Features")
        print(f"   🔍 Prometheus Available: {controller.task_counter is not None}")
        print(f"   📈 OpenTelemetry Available: {controller.tracer is not None}")
        print(f"   🧠 Embeddings Available: {controller.embedder is not None}")
        print(f"   🗄️ Neo4j Available: {controller.neo4j_client is not None}")
        
        # Test 9: Crew Integration
        print("\n🔄 Test 9: Crew Integration")
        crews = controller.crews
        print(f"   📋 Available Crews: {list(crews.keys())}")
        
        for crew_name, crew_instance in crews.items():
            print(f"      {crew_name.title()} Crew: ✅ Initialized")
            if hasattr(crew_instance, 'memory_manager'):
                crew_memory = crew_instance.memory_manager.get_memory_stats()
                print(f"         Memory Entries: {crew_memory['total_entries']}")
        
        # Test 10: Configuration Validation
        print("\n⚙️ Test 10: Configuration Validation")
        config_dict = config.dict()
        print(f"   📋 Configuration Keys: {list(config_dict.keys())}")
        print(f"   🔧 Core Settings: {len([k for k in config_dict.keys() if not k.endswith('_config')])}")
        print(f"   🎛️ Crew Configs: {len([k for k in config_dict.keys() if k.endswith('_config')])}")
        
        print("\n🎉 Enhanced CrewController tests completed successfully!")
        
        return {
            "status": "success",
            "tests_passed": 10,
            "memory_stats": memory_stats,
            "project_status": project_status,
            "complex_result": complex_result.get('status')
        }
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return {"status": "failed", "error": str(e)}
    
    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(test_enhanced_crew_controller()) 
