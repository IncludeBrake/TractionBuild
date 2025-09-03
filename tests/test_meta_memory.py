"""
Test script for ProjectMetaMemoryManager functionality.
"""

import asyncio
import tempfile
import shutil
from pathlib import Path
from src.tractionbuild.core.project_meta_memory import (
    ProjectMetaMemoryManager, 
    ProjectMetaMemory, 
    MemoryType, 
    MemoryPriority
)


async def test_meta_memory():
    """Test the project meta memory manager functionality."""

    # Create a temporary directory for testing
    temp_dir = Path(tempfile.mkdtemp())
    memory_file = temp_dir / "test_memory.json"
    
    try:
        # Initialize memory manager with test config
        config = ProjectMetaMemory(
            memory_file_path=str(memory_file),
            max_entries_per_type=100,
            memory_retention_days=30,
            auto_cleanup=True,
            backup_enabled=True
        )
        
        memory_manager = ProjectMetaMemoryManager(config)

        print("🧠 Testing ProjectMetaMemoryManager...")

        # Test 1: Add success pattern
        success_pattern = {
            "task_type": "market_research",
            "approach": "comprehensive_analysis",
            "result": "high_confidence_validation"
        }
        
        entry_id = memory_manager.add_success_pattern(
            pattern=success_pattern,
            project_id="test_project_1",
            agent_id="validator_agent",
            confidence_score=0.85
        )
        print(f"✅ Added success pattern: {entry_id}")

        # Test 2: Add failure pattern
        failure_pattern = {
            "task_type": "code_generation",
            "error": "token_limit_exceeded",
            "context": "large_codebase"
        }
        
        entry_id = memory_manager.add_failure_pattern(
            pattern=failure_pattern,
            project_id="test_project_2",
            agent_id="builder_agent",
            error_type="token_limit",
            confidence_score=0.75
        )
        print(f"❌ Added failure pattern: {entry_id}")

        # Test 3: Add heuristic
        heuristic = {
            "rule": "always_validate_market_size_before_building",
            "condition": "project_type == 'saas'",
            "action": "run_market_validation_first"
        }
        
        entry_id = memory_manager.add_heuristic(
            heuristic=heuristic,
            category="project_planning",
            confidence_score=0.8
        )
        print(f"💡 Added heuristic: {entry_id}")

        # Test 4: Add performance metric
        entry_id = memory_manager.add_performance_metric(
            metric_name="token_efficiency",
            value=0.92,
            context={
                "agent_id": "validator_agent",
                "project_id": "test_project_1",
                "task_type": "market_analysis"
            },
            confidence_score=0.95
        )
        print(f"📊 Added performance metric: {entry_id}")

        # Test 5: Get relevant patterns
        patterns = memory_manager.get_relevant_patterns(
            agent_id="validator_agent",
            context={"task_type": "market_research"},
            pattern_type="both"
        )
        
        print(f"🔍 Found patterns:")
        for pattern_type, entries in patterns.items():
            print(f"   - {pattern_type}: {len(entries)} entries")
            for entry in entries[:2]:  # Show first 2 entries
                print(f"     * {entry.content.get('context', 'N/A')} (confidence: {entry.confidence_score})")

        # Test 6: Get heuristics
        heuristics = memory_manager.get_heuristics(
            category="project_planning",
            limit=5
        )
        print(f"💡 Found {len(heuristics)} heuristics for project_planning")

        # Test 7: Get memory statistics
        stats = memory_manager.get_memory_stats()
        print(f"📈 Memory statistics:")
        print(f"   - Total entries: {stats['total_entries']}")
        print(f"   - Type counts: {stats['type_counts']}")
        print(f"   - Tag counts: {len(stats['tag_counts'])} tags")

        # Test 8: Test memory persistence
        print("💾 Testing memory persistence...")
        
        # Create new manager instance to test loading
        memory_manager2 = ProjectMetaMemoryManager(config)
        stats2 = memory_manager2.get_memory_stats()
        print(f"   - Loaded {stats2['total_entries']} entries from disk")

        # Test 9: Test filtering by tags
        tagged_entries = memory_manager.get_memory_entries(
            tags={"project:test_project_1"},
            limit=10
        )
        print(f"🏷️  Found {len(tagged_entries)} entries tagged with 'project:test_project_1'")

        # Test 10: Test priority filtering
        high_priority_entries = memory_manager.get_memory_entries(
            priority=MemoryPriority.HIGH,
            limit=10
        )
        print(f"⭐ Found {len(high_priority_entries)} high priority entries")

        print("🎉 Meta memory tests completed!")

    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(test_meta_memory()) 
