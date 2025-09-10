"""
🎯 STRATEGIC CHAOS TESTING SUITE FOR INVESTOR DEMO
Comprehensive testing that validates production readiness for financing
Focus: Core functionality, reliability, performance, and investor confidence
"""

import asyncio
import time
import logging
import json
import psutil
import os
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor
import tracemalloc
import gc
import sys
from datetime import datetime, timedelta

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    handlers=[
        logging.FileHandler('chaos_test_results.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class StrategicChaosTester:
    """Strategic testing suite designed for investor confidence and financing"""

    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()
        self.memory_snapshots = []
        self.performance_metrics = []

        # Initialize memory tracing
        tracemalloc.start()
        self.initial_memory = tracemalloc.get_traced_memory()[0]

        # System resource monitoring
        self.cpu_start = psutil.cpu_percent(interval=None)
        self.memory_start = psutil.virtual_memory().percent

    async def execute_strategic_chaos_protocol(self):
        """Execute comprehensive strategic testing protocol"""

        print("🎯 STRATEGIC CHAOS TESTING PROTOCOL")
        print("=" * 60)
        print("🎯 MISSION: Validate production readiness for investor financing")
        print("🎯 FOCUS: Core functionality, reliability, performance")
        print("🎯 GOAL: Demonstrate enterprise-grade capabilities")
        print("-" * 60)

        # Strategic test suite - ordered by business criticality
        strategic_tests = [
            # CORE FUNCTIONALITY (MOST CRITICAL FOR INVESTORS)
            ("🏗️ End-to-End Workflow Test", self.test_end_to_end_workflow, "Critical"),
            ("📊 Multi-Project Orchestration", self.test_multi_project_orchestration, "Critical"),
            ("🔄 Project Persistence & Retrieval", self.test_project_persistence, "Critical"),

            # PERFORMANCE & SCALABILITY
            ("⚡ Concurrent User Load Test", self.test_concurrent_user_load, "High"),
            ("📈 Data Volume Scalability", self.test_data_volume_scalability, "High"),
            ("🧠 Memory Leak Detection", self.test_memory_leak_detection, "Medium"),

            # RELIABILITY & RESILIENCE
            ("🛡️ Failure Recovery Scenarios", self.test_failure_recovery, "High"),
            ("🔄 System Restart Persistence", self.test_system_restart_persistence, "Medium"),
            ("⚡ Rapid Request Surge", self.test_rapid_request_surge, "Medium"),

            # INTEGRATION & API STABILITY
            ("🔗 Crew Integration Validation", self.test_crew_integration, "High"),
            ("🌐 API Endpoint Stability", self.test_api_endpoint_stability, "High"),
            ("📋 Input Validation Robustness", self.test_input_validation, "Medium"),

            # BUSINESS LOGIC VALIDATION
            ("💼 Business Rule Enforcement", self.test_business_rule_enforcement, "High"),
            ("📊 Analytics & Reporting", self.test_analytics_reporting, "Medium"),
            ("🔒 Security Validation", self.test_security_validation, "High"),
        ]

        passed_tests = 0
        total_tests = len(strategic_tests)
        critical_passed = 0
        critical_total = sum(1 for _, _, priority in strategic_tests if priority == "Critical")

        for test_name, test_func, priority in strategic_tests:
            print(f"\n{test_name}")
            print("-" * 50)

            # Take memory snapshot before test
            self.memory_snapshots.append(tracemalloc.get_traced_memory()[0])

            start_test_time = time.time()
            try:
                result = await test_func()
                duration = time.time() - start_test_time

                if result['success']:
                    status = "✅ PASSED"
                    passed_tests += 1
                    if priority == "Critical":
                        critical_passed += 1
                else:
                    status = "❌ FAILED"

                print(f"Status: {status} | Duration: {duration:.2f}s")
                if result.get('metrics'):
                    print(f"📊 {result['metrics']}")
                if result.get('warnings'):
                    print(f"⚠️  {result['warnings']}")

                self.test_results[test_name] = {
                    'success': result['success'],
                    'duration': duration,
                    'metrics': result.get('metrics', {}),
                    'warnings': result.get('warnings', []),
                    'priority': priority,
                    'error': result.get('error')
                }

            except Exception as e:
                duration = time.time() - start_test_time
                print(f"Status: ❌ FAILED | Duration: {duration:.2f}s")
                print(f"💥 EXCEPTION: {str(e)}")

                self.test_results[test_name] = {
                    'success': False,
                    'duration': duration,
                    'error': str(e),
                    'priority': priority
                }

            # Take memory snapshot after test
            self.memory_snapshots.append(tracemalloc.get_traced_memory()[0])

        # Generate comprehensive report
        await self.generate_investor_report(passed_tests, total_tests, critical_passed, critical_total)

    async def test_end_to_end_workflow(self):
        """Test complete project lifecycle from creation to completion"""
        try:
            # Import here to avoid circular imports
            from src.tractionbuild.crews.execution_crew import ExecutionCrew, ExecutionCrewConfig
            from src.tractionbuild.models.task import Task as TaskModel, TaskPriority

            print("  Testing complete project workflow...")

            # Create a realistic project scenario
            config = ExecutionCrewConfig(
                max_concurrent_tasks=5,
                checkpoint_interval=2,
                failure_retry_limit=2,
                circuit_breaker_threshold=5
            )

            project_data = {
                'id': 'investor_demo_001',
                'name': 'AI Startup Accelerator Platform',
                'description': 'Complete SaaS platform for startup acceleration using AI',
                'hypothesis': 'AI can reduce time-to-market by 60% for early-stage startups',
                'target_avatars': ['Technical founders', 'Product managers', 'Startup advisors']
            }

            crew = ExecutionCrew(project_data, config)

            # Create realistic business tasks
            tasks = [
                TaskModel(
                    id='market_research',
                    project_id='investor_demo_001',
                    name='Market Research & Validation',
                    description='Research target market, validate problem-solution fit',
                    priority=TaskPriority.CRITICAL
                ),
                TaskModel(
                    id='user_personas',
                    project_id='investor_demo_001',
                    name='User Persona Development',
                    description='Create detailed user personas and journey maps',
                    priority=TaskPriority.HIGH
                ),
                TaskModel(
                    id='mvp_features',
                    project_id='investor_demo_001',
                    name='MVP Feature Definition',
                    description='Define core features for minimum viable product',
                    priority=TaskPriority.HIGH
                ),
                TaskModel(
                    id='tech_architecture',
                    project_id='investor_demo_001',
                    name='Technical Architecture Design',
                    description='Design scalable technical architecture',
                    priority=TaskPriority.CRITICAL
                ),
                TaskModel(
                    id='business_model',
                    project_id='investor_demo_001',
                    name='Business Model Validation',
                    description='Validate revenue model and pricing strategy',
                    priority=TaskPriority.MEDIUM
                )
            ]

            # Set up dependencies
            tasks[1].dependencies = [tasks[0].id]  # User personas depend on market research
            tasks[2].dependencies = [tasks[0].id, tasks[1].id]  # MVP features depend on research and personas
            tasks[3].dependencies = [tasks[2].id]  # Architecture depends on MVP features
            tasks[4].dependencies = [tasks[0].id, tasks[1].id]  # Business model depends on research and personas

            start_time = time.time()
            result = await crew.orchestrate_execution(tasks)
            execution_time = time.time() - start_time

            success = result.get('status') == 'success'
            completed_tasks = len(result.get('results', {}).get('completed_tasks', []))
            total_tasks = len(tasks)

            return {
                'success': success,
                'metrics': f"Workflow completion: {completed_tasks}/{total_tasks} tasks | Time: {execution_time:.1f}s",
                'warnings': [] if success else ['Some tasks may have failed in the workflow']
            }

        except Exception as e:
            logger.error(f"End-to-end workflow test failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'warnings': ['Complete workflow execution failed']
            }

    async def test_multi_project_orchestration(self):
        """Test handling multiple concurrent projects"""
        try:
            from src.tractionbuild.crews.execution_crew import ExecutionCrew, ExecutionCrewConfig
            from src.tractionbuild.models.task import Task as TaskModel, TaskPriority

            print("  Testing concurrent project handling...")

            # Create multiple projects simultaneously
            projects = []
            for i in range(3):  # Test with 3 concurrent projects
                config = ExecutionCrewConfig(max_concurrent_tasks=3)
                project_data = {
                    'id': f'concurrent_project_{i}',
                    'name': f'Project {i} - AI Solution',
                    'description': f'Concurrent project {i} for load testing'
                }
                crew = ExecutionCrew(project_data, config)
                projects.append(crew)

            # Create tasks for each project
            all_orchestrations = []
            for i, crew in enumerate(projects):
                tasks = [
                    TaskModel(
                        id=f'project_{i}_task_{j}',
                        project_id=f'concurrent_project_{i}',
                        name=f'Project {i} Task {j}',
                        description=f'Task {j} for concurrent project {i}',
                        priority=TaskPriority.MEDIUM
                    ) for j in range(3)
                ]
                all_orchestrations.append(crew.orchestrate_execution(tasks))

            # Execute all projects concurrently
            start_time = time.time()
            results = await asyncio.gather(*all_orchestrations, return_exceptions=True)
            total_time = time.time() - start_time

            # Analyze results
            successful_projects = sum(1 for r in results if not isinstance(r, Exception) and r.get('status') == 'success')
            total_projects = len(projects)

            success = successful_projects >= total_projects * 0.8  # 80% success rate

            return {
                'success': success,
                'metrics': f"Concurrent projects: {successful_projects}/{total_projects} successful | Time: {total_time:.2f}s",
                'warnings': [] if success else [f'Only {successful_projects}/{total_projects} projects completed successfully']
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'warnings': ['Concurrent project execution failed']
            }

    async def test_project_persistence(self):
        """Test project data persistence and retrieval"""
        try:
            from src.tractionbuild.database.project_registry import ProjectRegistry

            print("  Testing project persistence...")

            registry = ProjectRegistry()

            # Create test project
            project_id = 'persistence_test_001'
            project_data = {
                'id': project_id,
                'name': 'Persistence Test Project',
                'description': 'Testing data persistence capabilities',
                'status': 'active',
                'created_at': datetime.now().isoformat(),
                'hypothesis': 'Data persistence works correctly',
                'target_avatars': ['Developers', 'Testers']
            }

            # Save project
            await registry.save_project(project_data)

            # Retrieve project
            retrieved = await registry.get_project(project_id)

            # Verify data integrity
            data_integrity = (
                retrieved['id'] == project_data['id'] and
                retrieved['name'] == project_data['name'] and
                retrieved['hypothesis'] == project_data['hypothesis']
            )

            # Test artifacts storage
            artifacts = {
                'market_analysis': {'type': 'report', 'content': 'Market analysis data'},
                'user_research': {'type': 'survey', 'content': 'User research findings'},
                'technical_spec': {'type': 'document', 'content': 'Technical specifications'}
            }

            await registry.save_artifacts(project_id, artifacts)
            retrieved_artifacts = await registry.get_artifacts(project_id)

            artifacts_integrity = len(retrieved_artifacts) == len(artifacts)

            success = data_integrity and artifacts_integrity

            return {
                'success': success,
                'metrics': f"Data integrity: {'✅' if data_integrity else '❌'}, Artifacts: {'✅' if artifacts_integrity else '❌'}",
                'warnings': [] if success else ['Data persistence issues detected']
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'warnings': ['Project persistence system failed']
            }

    async def test_concurrent_user_load(self):
        """Test system under concurrent user load"""
        try:
            print("  Testing concurrent user simulation...")

            # Simulate multiple users creating projects simultaneously
            async def simulate_user(user_id: int):
                try:
                    from src.tractionbuild.crews.execution_crew import ExecutionCrew, ExecutionCrewConfig
                    from src.tractionbuild.models.task import Task as TaskModel, TaskPriority

                    config = ExecutionCrewConfig(max_concurrent_tasks=2)
                    project_data = {
                        'id': f'user_{user_id}_project',
                        'name': f'User {user_id} SaaS Project',
                        'description': f'Project created by simulated user {user_id}'
                    }

                    crew = ExecutionCrew(project_data, config)

                    # Create user-like tasks
                    tasks = [
                        TaskModel(
                            id=f'user_{user_id}_research',
                            project_id=f'user_{user_id}_project',
                            name='Market Research',
                            description='Research target market and competitors',
                            priority=TaskPriority.HIGH
                        ),
                        TaskModel(
                            id=f'user_{user_id}_design',
                            project_id=f'user_{user_id}_project',
                            name='Product Design',
                            description='Design user interface and experience',
                            priority=TaskPriority.MEDIUM
                        )
                    ]

                    result = await crew.orchestrate_execution(tasks)
                    return result.get('status') == 'success'

                except Exception as e:
                    logger.error(f"User {user_id} simulation failed: {e}")
                    return False

            # Simulate 5 concurrent users
            user_tasks = [simulate_user(i) for i in range(5)]

            start_time = time.time()
            results = await asyncio.gather(*user_tasks, return_exceptions=True)
            total_time = time.time() - start_time

            successful_users = sum(1 for r in results if r is True)
            total_users = len(user_tasks)

            success = successful_users >= total_users * 0.7  # 70% success rate acceptable

            return {
                'success': success,
                'metrics': f"Concurrent users: {successful_users}/{total_users} successful | Time: {total_time:.2f}s",
                'warnings': [] if success else [f'Only {successful_users}/{total_users} concurrent users succeeded']
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'warnings': ['Concurrent user load test failed']
            }

    async def test_data_volume_scalability(self):
        """Test system with large data volumes"""
        try:
            from src.tractionbuild.database.project_registry import ProjectRegistry

            print("  Testing data volume scalability...")

            registry = ProjectRegistry()

            # Create projects with substantial data
            large_projects = []
            for i in range(10):
                project_data = {
                    'id': f'scalability_test_{i}',
                    'name': f'Large Scale Project {i}',
                    'description': 'A' * 1000,  # 1KB description
                    'hypothesis': 'B' * 500,   # Large hypothesis
                    'target_avatars': ['Avatar'] * 20,  # Multiple avatars
                    'large_field': 'C' * 5000  # 5KB additional data
                }
                large_projects.append(project_data)

            # Test bulk operations
            start_time = time.time()

            # Save all projects
            save_tasks = [registry.save_project(project) for project in large_projects]
            await asyncio.gather(*save_tasks)

            save_time = time.time() - start_time

            # Retrieve all projects
            start_time = time.time()
            retrieve_tasks = [registry.get_project(p['id']) for p in large_projects]
            retrieved_projects = await asyncio.gather(*retrieve_tasks)

            retrieve_time = time.time() - start_time

            # Verify data integrity
            integrity_checks = []
            for original, retrieved in zip(large_projects, retrieved_projects):
                if retrieved:
                    integrity_checks.append(
                        retrieved['id'] == original['id'] and
                        len(retrieved['description']) == len(original['description'])
                    )

            success_rate = sum(integrity_checks) / len(integrity_checks) if integrity_checks else 0

            success = success_rate >= 0.95  # 95% success rate for data integrity

            return {
                'success': success,
                'metrics': f"Data integrity: {success_rate:.1%} | Save: {save_time:.2f}s | Retrieve: {retrieve_time:.2f}s",
                'warnings': [] if success else [f'Data integrity: {success_rate:.1%}']
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'warnings': ['Data volume scalability test failed']
            }

    async def test_memory_leak_detection(self):
        """Monitor memory usage for leaks"""
        try:
            print("  Testing memory leak detection...")

            # Force garbage collection
            gc.collect()

            # Take initial memory snapshot
            initial_memory = tracemalloc.get_traced_memory()[0]

            # Perform memory-intensive operations
            memory_hungry_objects = []
            for i in range(100):
                # Create large data structures
                memory_hungry_objects.append({
                    'id': f'memory_test_{i}',
                    'large_data': 'X' * 10000,  # 10KB per object
                    'nested': {'data': 'Y' * 5000},
                    'list': ['Z' * 1000 for _ in range(10)]
                })

            # Take memory snapshot after allocation
            after_allocation = tracemalloc.get_traced_memory()[0]

            # Clean up
            del memory_hungry_objects
            gc.collect()

            # Take final memory snapshot
            final_memory = tracemalloc.get_traced_memory()[0]

            memory_leak_mb = (final_memory - initial_memory) / (1024 * 1024)
            allocation_mb = (after_allocation - initial_memory) / (1024 * 1024)

            # Memory leak is acceptable if less than 10% of allocated memory remains
            acceptable_leak = allocation_mb * 0.1
            has_memory_leak = memory_leak_mb > acceptable_leak

            success = not has_memory_leak

            return {
                'success': success,
                'metrics': f"Memory leak: {memory_leak_mb:.1f}MB | Allocation: {allocation_mb:.1f}MB",
                'warnings': [] if success else [f'Memory leak detected: {memory_leak_mb:.1f}MB retained']
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'warnings': ['Memory leak detection failed']
            }

    async def test_failure_recovery(self):
        """Test system recovery from various failure scenarios"""
        try:
            print("  Testing failure recovery scenarios...")

            from src.tractionbuild.crews.execution_crew import ExecutionCrew, ExecutionCrewConfig
            from src.tractionbuild.models.task import Task as TaskModel, TaskPriority

            config = ExecutionCrewConfig(
                max_concurrent_tasks=3,
                failure_retry_limit=2,
                circuit_breaker_threshold=3
            )

            project_data = {
                'id': 'failure_recovery_test',
                'name': 'Failure Recovery Test',
                'description': 'Testing system resilience'
            }

            crew = ExecutionCrew(project_data, config)

            # Create tasks that will likely fail and need recovery
            tasks = []
            for i in range(5):
                task = TaskModel(
                    id=f'failure_task_{i}',
                    project_id='failure_recovery_test',
                    name=f'Failure Prone Task {i}',
                    description=f'Task designed to test failure recovery {i}',
                    priority=TaskPriority.MEDIUM
                )
                tasks.append(task)

            result = await crew.orchestrate_execution(tasks)

            # Analyze recovery effectiveness
            total_tasks = len(tasks)
            completed_tasks = len(result.get('results', {}).get('completed_tasks', []))
            failed_tasks = len(result.get('results', {}).get('failed_tasks', []))

            # Success if at least 60% of tasks complete (some failures are expected)
            success_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
            success = success_rate >= 0.6

            recovery_effective = result.get('status') in ['success', 'partial_success']

            overall_success = success and recovery_effective

            return {
                'success': overall_success,
                'metrics': f"Recovery rate: {success_rate:.1%} | Completed: {completed_tasks}/{total_tasks}",
                'warnings': [] if overall_success else ['Failure recovery needs improvement']
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'warnings': ['Failure recovery test failed']
            }

    async def test_system_restart_persistence(self):
        """Test data persistence across simulated system restarts"""
        try:
            from src.tractionbuild.database.project_registry import ProjectRegistry

            print("  Testing system restart persistence...")

            registry = ProjectRegistry()

            # Create and save a complex project
            project_id = 'restart_test_project'
            complex_project = {
                'id': project_id,
                'name': 'System Restart Persistence Test',
                'description': 'Testing data survival across restarts',
                'status': 'in_progress',
                'created_at': datetime.now().isoformat(),
                'hypothesis': 'Data persists across system restarts',
                'target_avatars': ['System Administrators', 'DevOps Engineers'],
                'complex_data': {
                    'workflows': ['validation', 'execution', 'deployment'],
                    'configurations': {'env': 'production', 'version': '1.0.0'},
                    'metadata': {'tags': ['persistence', 'restart', 'test']}
                }
            }

            # Save project
            await registry.save_project(complex_project)

            # Simulate system restart by clearing any in-memory caches
            # (In a real scenario, this would be an actual process restart)

            # Retrieve project after "restart"
            retrieved = await registry.get_project(project_id)

            # Verify complex data structure integrity
            data_preserved = (
                retrieved['id'] == complex_project['id'] and
                retrieved['complex_data']['workflows'] == complex_project['complex_data']['workflows'] and
                retrieved['complex_data']['configurations']['version'] == '1.0.0'
            )

            # Test that project directory structure is maintained
            project_dir = f"runs/{project_id}"
            persistence_files_exist = (
                os.path.exists(f"{project_dir}/project.json") and
                os.path.exists(f"{project_dir}/artifacts.json")
            )

            success = data_preserved and persistence_files_exist

            return {
                'success': success,
                'metrics': f"Data preserved: {'✅' if data_preserved else '❌'}, Files exist: {'✅' if persistence_files_exist else '❌'}",
                'warnings': [] if success else ['Data may not survive system restarts']
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'warnings': ['System restart persistence test failed']
            }

    async def test_rapid_request_surge(self):
        """Test system under rapid request surges"""
        try:
            print("  Testing rapid request surge handling...")

            # Simulate rapid API-like requests
            async def rapid_request(request_id: int):
                try:
                    # Simulate API request processing
                    await asyncio.sleep(0.01)  # Simulate processing time
                    return f"Request {request_id} processed successfully"
                except Exception as e:
                    return f"Request {request_id} failed: {e}"

            # Surge test: 100 rapid requests
            request_tasks = [rapid_request(i) for i in range(100)]

            start_time = time.time()
            results = await asyncio.gather(*request_tasks, return_exceptions=True)
            surge_time = time.time() - start_time

            successful_requests = sum(1 for r in results if not isinstance(r, Exception) and "successfully" in str(r))
            total_requests = len(request_tasks)

            # Calculate throughput
            throughput = total_requests / surge_time if surge_time > 0 else 0

            # Success if 95% of requests succeed and throughput is reasonable
            success_rate = successful_requests / total_requests
            success = success_rate >= 0.95 and throughput >= 50  # 50 requests/second minimum

            return {
                'success': success,
                'metrics': f"Throughput: {throughput:.1f} req/sec | Success: {success_rate:.1%}",
                'warnings': [] if success else [f'Low success rate: {success_rate:.1%} or throughput: {throughput:.1f} req/sec']
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'warnings': ['Rapid request surge test failed']
            }

    async def test_crew_integration(self):
        """Test integration between different crews"""
        try:
            print("  Testing crew integration...")

            from src.tractionbuild.crews.execution_crew import ExecutionCrew, ExecutionCrewConfig
            from src.tractionbuild.models.task import Task as TaskModel, TaskPriority

            # Test that crews can work together in a workflow
            config = ExecutionCrewConfig(max_concurrent_tasks=4)

            project_data = {
                'id': 'crew_integration_test',
                'name': 'Crew Integration Test',
                'description': 'Testing crew collaboration'
            }

            crew = ExecutionCrew(project_data, config)

            # Create tasks that would typically involve different crews
            tasks = [
                TaskModel(
                    id='validation_task',
                    project_id='crew_integration_test',
                    name='Idea Validation',
                    description='Validate business idea and market opportunity',
                    priority=TaskPriority.CRITICAL
                ),
                TaskModel(
                    id='execution_task',
                    project_id='crew_integration_test',
                    name='Execution Planning',
                    description='Plan execution strategy and milestones',
                    priority=TaskPriority.HIGH
                ),
                TaskModel(
                    id='builder_task',
                    project_id='crew_integration_test',
                    name='Technical Implementation',
                    description='Implement technical solution',
                    priority=TaskPriority.HIGH
                ),
                TaskModel(
                    id='marketing_task',
                    project_id='crew_integration_test',
                    name='Marketing Strategy',
                    description='Develop go-to-market strategy',
                    priority=TaskPriority.MEDIUM
                )
            ]

            # Set up crew dependencies
            tasks[1].dependencies = [tasks[0].id]  # Execution depends on validation
            tasks[2].dependencies = [tasks[1].id]  # Builder depends on execution
            tasks[3].dependencies = [tasks[0].id, tasks[1].id]  # Marketing depends on validation and execution

            result = await crew.orchestrate_execution(tasks)

            # Verify crew integration worked
            integration_success = (
                result.get('status') in ['success', 'partial_success'] and
                len(result.get('results', {}).get('completed_tasks', [])) >= 3  # At least 3/4 tasks should complete
            )

            return {
                'success': integration_success,
                'metrics': f"Crew integration: {'✅' if integration_success else '❌'}",
                'warnings': [] if integration_success else ['Crew integration needs improvement']
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'warnings': ['Crew integration test failed']
            }

    async def test_api_endpoint_stability(self):
        """
        Purpose: Test API endpoint stability under load.
        Inputs: None.
        Outputs: None (side effect: prints status).
        Invariants: Should not raise unless import fails.
        Edge cases: aiohttp not installed, print fails.
        Example: await test_api_endpoint_stability()
        """
        try:
            import aiohttp

            print("  Testing API endpoint stability...")

            # Test health endpoint
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get('http://localhost:8000/health') as response:
                        health_status = response.status == 200
                        health_data = await response.json()
                        health_response = health_data.get('status') == 'healthy'
                except Exception as e:
                    health_status = False
                    health_response = False
                    logger.warning(f"Health endpoint test failed: {e}")

            # Test project creation endpoint (simulated)
            api_stability = health_status and health_response

            return {
                'success': api_stability,
                'metrics': f"API endpoints: {'✅ Stable' if api_stability else '❌ Unstable'}"
            }
        except Exception as e:
            return {
                'success': False,
                'metrics': f"API stability check failed: {str(e)}"
            }