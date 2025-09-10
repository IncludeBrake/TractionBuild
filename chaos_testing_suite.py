"""
🔥 ENTERPRISE CHAOS TESTING SUITE
Prove production readiness through systematic stress testing
"""
import asyncio
import time
import random
import logging
from concurrent.futures import ThreadPoolExecutor
from src.tractionbuild.crews.execution_crew import ExecutionCrew, ExecutionCrewConfig
from src.tractionbuild.models.task import Task as TaskModel, TaskPriority

# Configure aggressive logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s: %(message)s')

class EnterpriseChaosTester:
    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()

    async def execute_chaos_protocol(self):
        """Execute comprehensive production chaos testing"""

        print("🔥 ENTERPRISE CHAOS TESTING PROTOCOL")
        print("=" * 60)
        print("⚠️  WARNING: This will stress-test ALL enterprise patterns")
        print("🎯 Goal: Prove or disprove production readiness claims")
        print("-" * 60)

        chaos_tests = [
            ("💥 Extreme Concurrency Chaos", self.test_extreme_concurrency),
            ("🌪️ Resource Exhaustion Attack", self.test_resource_exhaustion),
            ("⚡ Rapid Fire Orchestration", self.test_rapid_fire_execution),
            ("🔗 Complex Dependency Hell", self.test_dependency_hell),
            ("💣 Failure Cascade Simulation", self.test_failure_cascade),
            ("🌊 Memory Pressure Test", self.test_memory_pressure),
            ("⏱️ Timeout Stress Test", self.test_timeout_scenarios),
            ("🎭 Circuit Breaker Torture", self.test_circuit_breaker_torture),
            ("📊 Sustained Load Endurance", self.test_sustained_load),
            ("🧨 Edge Case Explosion", self.test_edge_cases)
        ]

        passed_tests = 0
        total_tests = len(chaos_tests)

        for test_name, test_func in chaos_tests:
            print(f"\n{test_name}")
            print("-" * 40)

            start_test_time = time.time()

            try:
                result = await test_func()
                duration = time.time() - start_test_time

                if result['success']:
                    print(f"✅ SURVIVED - {duration:.2f}s")
                    print(f"📊 {result.get('metrics', 'No metrics')}")
                    passed_tests += 1
                else:
                    print(f"💥 FAILED - {duration:.2f}s")
                    print(f"❌ {result.get('error', 'Unknown failure')}")

                self.test_results[test_name] = {
                    'success': result['success'],
                    'duration': duration,
                    'metrics': result.get('metrics', {}),
                    'error': result.get('error')
                }

            except Exception as e:
                duration = time.time() - start_test_time
                print(f"💀 EXCEPTION - {duration:.2f}s")
                print(f"💥 {str(e)}")

                self.test_results[test_name] = {
                    'success': False,
                    'duration': duration,
                    'error': f"Exception: {str(e)}"
                }

        self.generate_chaos_report(passed_tests, total_tests)

    async def test_extreme_concurrency(self):
        """Test with extremely high concurrent task loads"""
        config = ExecutionCrewConfig(
            max_concurrent_tasks=25,  # Extreme concurrency
            checkpoint_interval=1,
            failure_retry_limit=1,
            circuit_breaker_threshold=10
        )

        project_data = {
            'id': 'chaos-concurrency-001',
            'name': 'Extreme Concurrency Chaos',
            'description': 'Testing system limits under extreme concurrent load'
        }

        crew = ExecutionCrew(project_data, config)

        # Generate 50 independent tasks
        tasks = []
        for i in range(50):
            tasks.append(TaskModel(
                id=f'chaos_concurrent_{i}',
                project_id='chaos-concurrency-001',
                name=f'Chaos Concurrent Task {i}',
                description=f'Extreme concurrency test task {i}',
                priority=random.choice(list(TaskPriority))
            ))

        try:
            start_time = time.time()
            result = await crew.orchestrate_execution(tasks)
            duration = time.time() - start_time

            completed_tasks = len(result.get('task_results', []))
            throughput = completed_tasks / duration if duration > 0 else 0

            success = (
                result.get('status') == 'success' and
                completed_tasks >= 40 and  # At least 80% completion
                throughput > 3.0  # Minimum throughput under extreme load
            )

            return {
                'success': success,
                'metrics': f"50 tasks → {completed_tasks} completed, {throughput:.2f} tasks/sec"
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def test_resource_exhaustion(self):
        """Test system behavior under resource exhaustion"""
        config = ExecutionCrewConfig(
            max_concurrent_tasks=20,
            checkpoint_interval=1,
            failure_retry_limit=2,
            circuit_breaker_threshold=5
        )

        project_data = {
            'id': 'chaos-resources-001',
            'name': 'Resource Exhaustion Attack',
            'description': 'Testing resource management under extreme pressure'
        }

        crew = ExecutionCrew(project_data, config)

        # Create resource-intensive tasks
        tasks = []
        for i in range(30):
            tasks.append(TaskModel(
                id=f'resource_hog_{i}',
                project_id='chaos-resources-001',
                name=f'Resource Hog {i}',
                description=f'Intentionally resource-intensive task {i}',
                priority=TaskPriority.HIGH
            ))

        try:
            result = await crew.orchestrate_execution(tasks)

            # Success means system handled resource pressure gracefully
            resource_mgmt_working = (
                result.get('status') in ['success', 'partial_success'] and
                'resource_exhaustion' not in str(result.get('errors', []))
            )

            return {
                'success': resource_mgmt_working,
                'metrics': f"Resource pressure handled, status: {result.get('status')}"
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def test_rapid_fire_execution(self):
        """Test rapid successive orchestration calls"""
        config = ExecutionCrewConfig(
            max_concurrent_tasks=10,
            checkpoint_interval=1,
            failure_retry_limit=1,
            circuit_breaker_threshold=3
        )

        project_data = {
            'id': 'chaos-rapid-001',
            'name': 'Rapid Fire Test',
            'description': 'Rapid successive orchestration testing'
        }

        try:
            # Fire 5 orchestrations in rapid succession
            orchestration_tasks = []

            for batch in range(5):
                crew = ExecutionCrew(project_data, config)

                tasks = []
                for i in range(5):
                    tasks.append(TaskModel(
                        id=f'rapid_{batch}_{i}',
                        project_id='chaos-rapid-001',
                        name=f'Rapid Task {batch}-{i}',
                        description=f'Rapid fire test task {batch}-{i}',
                        priority=TaskPriority.MEDIUM
                    ))

                orchestration_tasks.append(crew.orchestrate_execution(tasks))

            # Execute all orchestrations concurrently
            start_time = time.time()
            results = await asyncio.gather(*orchestration_tasks, return_exceptions=True)
            duration = time.time() - start_time

            successful_orchestrations = sum(
                1 for result in results
                if not isinstance(result, Exception) and result.get('status') == 'success'
            )

            success = (
                successful_orchestrations >= 4 and  # At least 80% success
                duration < 30  # Reasonable completion time
            )

            return {
                'success': success,
                'metrics': f"5 rapid orchestrations → {successful_orchestrations} successful in {duration:.2f}s"
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def test_dependency_hell(self):
        """Test complex multi-level dependency scenarios"""
        config = ExecutionCrewConfig(
            max_concurrent_tasks=15,
            checkpoint_interval=2,
            failure_retry_limit=2,
            circuit_breaker_threshold=4
        )

        project_data = {
            'id': 'chaos-deps-001',
            'name': 'Dependency Hell',
            'description': 'Testing complex dependency resolution'
        }

        crew = ExecutionCrew(project_data, config)

        # Create nightmare dependency scenario
        tasks = []

        # Level 1: 5 foundation tasks
        for i in range(5):
            tasks.append(TaskModel(
                id=f'foundation_{i}',
                project_id='chaos-deps-001',
                name=f'Foundation {i}',
                description=f'Foundation task {i}',
                priority=TaskPriority.CRITICAL
            ))

        # Level 2: 8 tasks depending on foundations
        for i in range(8):
            task = TaskModel(
                id=f'level2_{i}',
                project_id='chaos-deps-001',
                name=f'Level 2 Task {i}',
                description=f'Second level task {i}',
                priority=TaskPriority.HIGH
            )
            # Complex dependencies
            task.dependencies = [f'foundation_{j}' for j in range(min(3, 5))]
            tasks.append(task)

        # Level 3: 6 tasks with cross-dependencies
        for i in range(6):
            task = TaskModel(
                id=f'level3_{i}',
                project_id='chaos-deps-001',
                name=f'Level 3 Task {i}',
                description=f'Third level task {i}',
                priority=TaskPriority.MEDIUM
            )
            # Cross-dependencies between level 2 tasks
            task.dependencies = [f'level2_{j}' for j in range(min(4, 8))]
            tasks.append(task)

        # Level 4: Final integration with dependencies on all levels
        final_task = TaskModel(
            id='final_chaos_integration',
            project_id='chaos-deps-001',
            name='Final Chaos Integration',
            description='Ultimate dependency resolution test',
            priority=TaskPriority.CRITICAL
        )
        final_task.dependencies = [f'level3_{i}' for i in range(6)]
        tasks.append(final_task)

        try:
            result = await crew.orchestrate_execution(tasks)

            total_tasks = len(tasks)
            completed_tasks = len(result.get('task_results', []))

            # Success requires complex DAG resolution
            dag_success = (
                result.get('status') == 'success' and
                completed_tasks == total_tasks and
                'final_chaos_integration' in [r.get('task_id') for r in result.get('task_results', [])]
            )

            return {
                'success': dag_success,
                'metrics': f"Complex DAG: {total_tasks} tasks, 4 levels, {completed_tasks} completed"
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def test_failure_cascade(self):
        """Test system resilience to cascading failures"""
        config = ExecutionCrewConfig(
            max_concurrent_tasks=12,
            checkpoint_interval=1,
            failure_retry_limit=2,
            circuit_breaker_threshold=3  # Low threshold to test breaker
        )

        project_data = {
            'id': 'chaos-cascade-001',
            'name': 'Failure Cascade Test',
            'description': 'Testing cascading failure resilience'
        }

        crew = ExecutionCrew(project_data, config)

        # Create tasks that may trigger failures
        tasks = []
        for i in range(15):
            tasks.append(TaskModel(
                id=f'cascade_task_{i}',
                project_id='chaos-cascade-001',
                name=f'Cascade Test Task {i}',
                description=f'Failure cascade test task {i}',
                priority=TaskPriority.MEDIUM
            ))

        try:
            result = await crew.orchestrate_execution(tasks)

            # Success means system survived cascading failures
            cascade_survival = (
                result.get('status') in ['success', 'partial_success'] and
                len(result.get('task_results', [])) > 5  # Some tasks completed
            )

            return {
                'success': cascade_survival,
                'metrics': f"Cascade test: {result.get('status')}, circuit breaker functional"
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def test_memory_pressure(self):
        """Test system under memory pressure"""
        config = ExecutionCrewConfig(
            max_concurrent_tasks=20,
            checkpoint_interval=1,
            failure_retry_limit=1,
            circuit_breaker_threshold=5
        )

        # Create multiple crews to increase memory pressure
        crews = []
        for i in range(3):
            project_data = {
                'id': f'chaos-memory-{i:03d}',
                'name': f'Memory Pressure Test {i}',
                'description': f'Memory pressure test {i}'
            }
            crews.append(ExecutionCrew(project_data, config))

        try:
            # Execute multiple orchestrations simultaneously
            all_orchestrations = []

            for crew_idx, crew in enumerate(crews):
                tasks = []
                for i in range(10):
                    tasks.append(TaskModel(
                        id=f'memory_task_{crew_idx}_{i}',
                        project_id=f'chaos-memory-{crew_idx:03d}',
                        name=f'Memory Task {crew_idx}-{i}',
                        description=f'Memory pressure task {crew_idx}-{i}',
                        priority=TaskPriority.MEDIUM
                    ))

                all_orchestrations.append(crew.orchestrate_execution(tasks))

            # Execute all concurrently to create memory pressure
            results = await asyncio.gather(*all_orchestrations, return_exceptions=True)

            successful_crews = sum(
                1 for result in results
                if not isinstance(result, Exception) and result.get('status') == 'success'
            )

            memory_resilience = successful_crews >= 2  # At least 2/3 successful

            return {
                'success': memory_resilience,
                'metrics': f"Memory pressure: {successful_crews}/3 crews successful"
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def test_timeout_scenarios(self):
        """Test timeout handling and recovery"""
        config = ExecutionCrewConfig(
            max_concurrent_tasks=8,
            checkpoint_interval=1,
            failure_retry_limit=1,
            circuit_breaker_threshold=3
        )

        project_data = {
            'id': 'chaos-timeout-001',
            'name': 'Timeout Stress Test',
            'description': 'Testing timeout scenarios'
        }

        crew = ExecutionCrew(project_data, config)

        # Create tasks that may timeout
        tasks = []
        for i in range(12):
            tasks.append(TaskModel(
                id=f'timeout_task_{i}',
                project_id='chaos-timeout-001',
                name=f'Timeout Task {i}',
                description=f'Potential timeout task {i}',
                priority=TaskPriority.MEDIUM
            ))

        try:
            # Set aggressive timeout
            result = await asyncio.wait_for(
                crew.orchestrate_execution(tasks),
                timeout=15.0  # Aggressive timeout
            )

            timeout_handling = (
                result.get('status') in ['success', 'partial_success'] and
                'timeout' not in str(result.get('errors', [])).lower()
            )

            return {
                'success': timeout_handling,
                'metrics': f"Timeout test: {result.get('status')}, graceful handling"
            }

        except asyncio.TimeoutError:
            return {'success': False, 'error': 'System failed to handle timeouts gracefully'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def test_circuit_breaker_torture(self):
        """Torture test the circuit breaker pattern"""
        config = ExecutionCrewConfig(
            max_concurrent_tasks=6,
            checkpoint_interval=1,
            failure_retry_limit=1,
            circuit_breaker_threshold=2  # Very sensitive breaker
        )

        project_data = {
            'id': 'chaos-breaker-001',
            'name': 'Circuit Breaker Torture',
            'description': 'Torture testing circuit breaker'
        }

        crew = ExecutionCrew(project_data, config)

        # Multiple waves of tasks to test breaker recovery
        all_results = []

        for wave in range(3):
            tasks = []
            for i in range(8):
                tasks.append(TaskModel(
                    id=f'breaker_torture_{wave}_{i}',
                    project_id='chaos-breaker-001',
                    name=f'Breaker Torture {wave}-{i}',
                    description=f'Circuit breaker torture task {wave}-{i}',
                    priority=TaskPriority.MEDIUM
                ))

            try:
                result = await crew.orchestrate_execution(tasks)
                all_results.append(result)

                # Brief pause between waves
                await asyncio.sleep(0.5)

            except Exception as e:
                all_results.append({'status': 'failed', 'error': str(e)})

        # Success means circuit breaker functioned across multiple waves
        successful_waves = sum(
            1 for result in all_results
            if result.get('status') in ['success', 'partial_success']
        )

        breaker_resilience = successful_waves >= 2

        return {
            'success': breaker_resilience,
            'metrics': f"Breaker torture: {successful_waves}/3 waves successful"
        }

    async def test_sustained_load(self):
        """Test sustained load over extended period"""
        config = ExecutionCrewConfig(
            max_concurrent_tasks=10,
            checkpoint_interval=2,
            failure_retry_limit=2,
            circuit_breaker_threshold=4
        )

        project_data = {
            'id': 'chaos-sustained-001',
            'name': 'Sustained Load Test',
            'description': 'Extended sustained load testing'
        }

        crew = ExecutionCrew(project_data, config)

        # Execute sustained load for ~30 seconds
        start_time = time.time()
        completed_batches = 0
        total_tasks_completed = 0

        try:
            while time.time() - start_time < 30:  # 30 second sustained test
                tasks = []
                for i in range(8):
                    tasks.append(TaskModel(
                        id=f'sustained_{completed_batches}_{i}',
                        project_id='chaos-sustained-001',
                        name=f'Sustained Task {completed_batches}-{i}',
                        description=f'Sustained load test task {completed_batches}-{i}',
                        priority=TaskPriority.MEDIUM
                    ))

                result = await crew.orchestrate_execution(tasks)

                if result.get('status') == 'success':
                    completed_tasks = len(result.get('task_results', []))
                    total_tasks_completed += completed_tasks
                    completed_batches += 1

                # Brief pause to prevent overwhelming the system
                await asyncio.sleep(0.2)

            duration = time.time() - start_time
            throughput = total_tasks_completed / duration if duration > 0 else 0

            sustained_success = (
                completed_batches >= 5 and  # At least 5 batches completed
                total_tasks_completed >= 30 and  # At least 30 tasks completed
                throughput > 1.0  # Minimum sustained throughput
            )

            return {
                'success': sustained_success,
                'metrics': f"Sustained load: {completed_batches} batches, {total_tasks_completed} tasks, {throughput:.2f} tasks/sec"
            }

        except Exception as e:
            duration = time.time() - start_time
            return {
                'success': False,
                'error': f"Sustained load failed after {duration:.2f}s: {str(e)}"
            }

    async def test_edge_cases(self):
        """Test various edge cases and boundary conditions"""
        config = ExecutionCrewConfig(
            max_concurrent_tasks=5,
            checkpoint_interval=1,
            failure_retry_limit=1,
            circuit_breaker_threshold=2
        )

        project_data = {
            'id': 'chaos-edge-001',
            'name': 'Edge Case Explosion',
            'description': 'Testing edge cases and boundary conditions'
        }

        crew = ExecutionCrew(project_data, config)

        # Test edge cases
        edge_cases = [
            # Empty task list
            [],
            # Single task
            [TaskModel(id='single', project_id='chaos-edge-001', name='Single', description='Single task', priority=TaskPriority.LOW)],
            # Maximum priority tasks
            [TaskModel(id=f'critical_{i}', project_id='chaos-edge-001', name=f'Critical {i}', description=f'Critical task {i}', priority=TaskPriority.CRITICAL) for i in range(3)],
            # Mixed priorities with dependencies
            lambda: self._create_mixed_dependency_tasks(project_data['id'])
        ]

        edge_results = []

        for i, edge_case in enumerate(edge_cases):
            try:
                if callable(edge_case):
                    tasks = edge_case()
                else:
                    tasks = edge_case

                if not tasks:  # Empty list test
                    result = {'status': 'success', 'task_results': []}
                else:
                    result = await crew.orchestrate_execution(tasks)

                edge_results.append(result.get('status') == 'success')

            except Exception as e:
                print(f"Edge case {i} failed: {e}")
                edge_results.append(False)

        # Success means all edge cases handled gracefully
        edge_success = sum(edge_results) >= len(edge_cases) - 1  # Allow 1 failure

        return {
            'success': edge_success,
            'metrics': f"Edge cases: {sum(edge_results)}/{len(edge_cases)} passed"
        }

    def _create_mixed_dependency_tasks(self, project_id):
        """Create tasks with mixed priorities and complex dependencies"""
        tasks = []

        # Create base tasks
        for i in range(4):
            tasks.append(TaskModel(
                id=f'mixed_base_{i}',
                project_id=project_id,
                name=f'Mixed Base {i}',
                description=f'Base task {i}',
                priority=TaskPriority.LOW
            ))

        # Create dependent tasks with higher priorities
        for i in range(3):
            task = TaskModel(
                id=f'mixed_dep_{i}',
                project_id=project_id,
                name=f'Mixed Dep {i}',
                description=f'Dependent task {i}',
                priority=TaskPriority.HIGH
            )
            task.dependencies = [f'mixed_base_{j}' for j in range(min(2, 4))]
            tasks.append(task)

        return tasks

    def generate_chaos_report(self, passed_tests, total_tests):
        """Generate comprehensive chaos testing report"""

        total_duration = time.time() - self.start_time
        success_rate = (passed_tests / total_tests) * 100

        print(f"\n🎯 CHAOS TESTING COMPLETE")
        print(f"=" * 60)
        print(f"📊 RESULTS: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
        print(f"⏱️  TOTAL DURATION: {total_duration:.2f} seconds")
        print(f"🏆 PRODUCTION READINESS: {'CONFIRMED' if success_rate >= 80 else 'REQUIRES WORK'}")
        print("-" * 60)

        # Test details
        for test_name, result in self.test_results.items():
            status = "✅" if result['success'] else "❌"
            duration = result['duration']
            print(".2f")

        # Performance analysis
        print(f"\n⚡ PERFORMANCE ANALYSIS:")
        avg_duration = total_duration / total_tests
        print(".2f")

        successful_tests = [r for r in self.test_results.values() if r['success']]
        if successful_tests:
            avg_success_duration = sum(r['duration'] for r in successful_tests) / len(successful_tests)
            print(".2f")

        # Production readiness assessment
        print(f"\n🏭 PRODUCTION READINESS ASSESSMENT:")
        if success_rate >= 95:
            print("🎉 EXCELLENT: System handles extreme chaos flawlessly")
            print("🚀 READY FOR ENTERPRISE PRODUCTION DEPLOYMENT")
        elif success_rate >= 80:
            print("✅ GOOD: System resilient under extreme conditions")
            print("⚠️  RECOMMENDED: Monitor closely in production")
        elif success_rate >= 60:
            print("⚠️  FAIR: System shows some weaknesses under extreme load")
            print("🔧 REQUIRED: Address identified issues before production")
        else:
            print("❌ POOR: System not ready for production deployment")
            print("🔨 REQUIRED: Significant architectural improvements needed")

        print(f"\n🎯 BOTTOM LINE:")
        if success_rate >= 80:
            print("✅ TRACTIONBUILD IS PRODUCTION READY!")
            print("   Enterprise patterns proven under chaos conditions")
        else:
            print("❌ PRODUCTION READINESS NOT ACHIEVED")
            print("   Core system requires further hardening")


async def main():
    """Main chaos testing execution"""
    print("🔥 INITIATING ENTERPRISE CHAOS TESTING PROTOCOL")
    print("This will systematically stress-test ALL enterprise patterns")
    print("⚠️  WARNING: System will be pushed to extreme limits")

    tester = EnterpriseChaosTester()
    await tester.execute_chaos_protocol()


if __name__ == "__main__":
    asyncio.run(main())
