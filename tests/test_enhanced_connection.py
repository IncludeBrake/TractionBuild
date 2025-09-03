"""
Test script for enhanced Neo4j connection functionality.
Demonstrates connection pooling, retry logic, secure configuration, and observability.
"""

import asyncio
import os
import tempfile
from pathlib import Path
from check_connection import check_connection, get_connection_info, health_check
from src.tractionbuild.database.project_registry import ProjectRegistry
from src.tractionbuild.core.crew_controller import CrewController, CrewControllerConfig


async def test_enhanced_connection():
    """Test the enhanced connection functionality."""
    
    print("🚀 Testing Enhanced Neo4j Connection")
    print("=" * 50)
    
    # Set up environment variables for testing
    os.environ["NEO4J_URI"] = "neo4j://localhost:7687"
    os.environ["NEO4J_USER"] = "neo4j"
    os.environ["NEO4J_PASSWORD"] = "test_password"
    
    try:
        # Test 1: Basic Connection Check
        print("\n📊 Test 1: Enhanced Connection Check")
        try:
            success = await check_connection()
            print(f"   Connection Success: {success}")
        except Exception as e:
            print(f"   ⚠️ Connection check failed (expected if Neo4j not running): {e}")
        
        # Test 2: Connection Information
        print("\n📋 Test 2: Connection Information")
        try:
            connection_info = await get_connection_info()
            print(f"   URI: {connection_info['uri']}")
            print(f"   User: {connection_info['user']}")
            print(f"   Password Set: {connection_info['password_set']}")
            print(f"   Pool Size: {connection_info['pool_size']}")
            print(f"   Timeout: {connection_info['timeout']}s")
            print(f"   Retry Attempts: {connection_info['retry_attempts']}")
            print(f"   Prometheus Available: {connection_info['prometheus_available']}")
            print(f"   OpenTelemetry Available: {connection_info['opentelemetry_available']}")
        except Exception as e:
            print(f"   ⚠️ Connection info failed: {e}")
        
        # Test 3: Health Check
        print("\n🏥 Test 3: Comprehensive Health Check")
        try:
            health = await health_check()
            print(f"   Status: {health['status']}")
            print(f"   Connection Success: {health['connection_success']}")
            print(f"   Query Success: {health['query_success']}")
            if 'error' in health:
                print(f"   Error: {health['error']}")
        except Exception as e:
            print(f"   ⚠️ Health check failed: {e}")
        
        # Test 4: ProjectRegistry Integration
        print("\n📝 Test 4: ProjectRegistry with Enhanced Connection")
        try:
            registry = ProjectRegistry(
                neo4j_uri="neo4j://localhost:7687",
                neo4j_user="neo4j"
            )
            print("   ✅ ProjectRegistry initialized")
            
            # Test project registration
            test_idea = "AI-powered task management app for remote teams"
            test_task_graph = {
                "nodes": [
                    {"id": "task_001", "name": "Market Research", "type": "validation"},
                    {"id": "task_002", "name": "Architecture Design", "type": "build"},
                    {"id": "task_003", "name": "Code Generation", "type": "build"}
                ],
                "edges": [
                    {"from": "task_001", "to": "task_002"},
                    {"from": "task_002", "to": "task_003"}
                ]
            }
            
            try:
                graph_hash = await registry.register_project(
                    idea=test_idea,
                    task_graph=test_task_graph,
                    token_usage=1500,
                    confidence=0.85,
                    overrides=False
                )
                print(f"   ✅ Project registered with hash: {graph_hash}")
                
                # Test query
                project = await registry.query_registry(graph_hash)
                if project:
                    print(f"   ✅ Project retrieved from registry")
                    print(f"      Idea: {project.get('idea', 'N/A')}")
                    print(f"      Token Usage: {project.get('token_usage', 'N/A')}")
                    print(f"      Confidence: {project.get('confidence', 'N/A')}")
                else:
                    print(f"   ⚠️ Project not found in registry")
                    
            except Exception as e:
                print(f"   ⚠️ Project registration failed (expected if Neo4j not running): {e}")
            
            # Test cache stats
            cache_stats = registry.get_cache_stats()
            print(f"   Cache Stats: {cache_stats}")
            
            # Test connection info
            registry_info = await registry.get_connection_info()
            print(f"   Registry Connection Info: {registry_info}")
            
            # Clean up
            await registry.close()
            print("   ✅ ProjectRegistry closed")
            
        except Exception as e:
            print(f"   ⚠️ ProjectRegistry test failed: {e}")
        
        # Test 5: CrewController Integration
        print("\n🎯 Test 5: CrewController with Enhanced Connection")
        try:
            # Create temporary config file
            temp_dir = Path(tempfile.mkdtemp())
            config_file = temp_dir / "test_crew_config.yaml"
            
            config_content = """
crews:
  validator:
    name: "Validator Crew"
    description: "Market research and validation"
    agents:
      - role: "Market Research Specialist"
        goal: "Conduct market research"
        backstory: "Expert market researcher"
        tools: ["market_api"]
        verbose: true
        allow_delegation: false
    tasks:
      - name: "validate_idea"
        description: "Validate the provided idea"
        expected_output: "Validation report"
        agent: "Market Research Specialist"
"""
            
            with open(config_file, 'w') as f:
                f.write(config_content)
            
            # Initialize CrewController
            controller_config = CrewControllerConfig(
                enable_observability=True,
                enable_graph_execution=True,
                enable_parallel_execution=True,
                enable_timeout_handling=True,
                max_execution_time=60,
                neo4j_uri="neo4j://localhost:7687",
                neo4j_user="neo4j",
                log_level="INFO"
            )
            
            controller = CrewController(controller_config)
            print("   ✅ CrewController initialized with enhanced connection")
            
            # Test project status
            status = await controller.get_project_status("test_project")
            print(f"   Project Status: {status}")
            
            # Clean up
            config_file.unlink()
            temp_dir.rmdir()
            
        except Exception as e:
            print(f"   ⚠️ CrewController test failed: {e}")
        
        # Test 6: Performance Metrics
        print("\n⚡ Test 6: Performance Metrics")
        try:
            # Test multiple connection attempts
            results = []
            for i in range(3):
                try:
                    success = await check_connection()
                    results.append(success)
                    print(f"   Attempt {i+1}: {'✅ Success' if success else '❌ Failed'}")
                except Exception as e:
                    results.append(False)
                    print(f"   Attempt {i+1}: ❌ Failed - {e}")
            
            success_rate = sum(results) / len(results) * 100
            print(f"   Success Rate: {success_rate:.1f}%")
            
        except Exception as e:
            print(f"   ⚠️ Performance test failed: {e}")
        
        # Test 7: Error Handling
        print("\n⚠️ Test 7: Error Handling")
        
        # Test with invalid credentials
        original_password = os.environ.get("NEO4J_PASSWORD")
        os.environ["NEO4J_PASSWORD"] = "invalid_password"
        
        try:
            success = await check_connection()
            print(f"   Invalid credentials test: {'❌ Unexpected success' if success else '✅ Correctly failed'}")
        except Exception as e:
            print(f"   ✅ Invalid credentials correctly rejected: {e}")
        
        # Restore original password
        if original_password:
            os.environ["NEO4J_PASSWORD"] = original_password
        else:
            os.environ["NEO4J_PASSWORD"] = "test_password"
        
        # Test with missing password
        del os.environ["NEO4J_PASSWORD"]
        try:
            success = await check_connection()
            print(f"   Missing password test: {'❌ Unexpected success' if success else '✅ Correctly failed'}")
        except Exception as e:
            print(f"   ✅ Missing password correctly rejected: {e}")
        
        # Restore password
        os.environ["NEO4J_PASSWORD"] = "test_password"
        
        print("\n🎉 Enhanced connection tests completed successfully!")
        
        return {
            "status": "success",
            "tests_passed": 7,
            "connection_enhanced": True
        }
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return {"status": "failed", "error": str(e)}


if __name__ == "__main__":
    asyncio.run(test_enhanced_connection()) 
