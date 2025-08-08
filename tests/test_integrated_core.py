"""
Integrated test script for core ZeroToShip components.
Demonstrates TokenBudgetManager, OutputValidator, and ProjectMetaMemoryManager working together.
"""

import asyncio
import tempfile
import shutil
from pathlib import Path
from src.zerotoship.core.token_budget import TokenBudgetManager, BudgetLevel, BudgetAction
from src.zerotoship.core.output_validator import OutputValidator, OutputValidatorConfig, ValidationSeverity
from src.zerotoship.core.project_meta_memory import (
    ProjectMetaMemoryManager, 
    ProjectMetaMemory, 
    MemoryType, 
    MemoryPriority
)


async def test_integrated_core():
    """Test all core components working together."""

    # Create a temporary directory for testing
    temp_dir = Path(tempfile.mkdtemp())
    memory_file = temp_dir / "integrated_memory.json"
    
    try:
        print("🚀 Testing Integrated Core Components...")

        # Initialize all core components
        print("\n📦 Initializing core components...")
        
        # 1. Token Budget Manager
        budget_manager = TokenBudgetManager(
            per_agent_limit=5000,
            per_crew_limit=20000,
            per_run_limit=50000,
            enable_budgeting=True,
            enable_cost_tracking=True
        )
        print("✅ TokenBudgetManager initialized")

        # 2. Output Validator
        validator_config = OutputValidatorConfig(
            enable_hallucination_detection=True,
            enable_security_checks=True,
            enable_format_validation=True,
            max_content_length=1000
        )
        output_validator = OutputValidator(validator_config)
        print("✅ OutputValidator initialized")

        # 3. Project Meta Memory Manager
        memory_config = ProjectMetaMemory(
            memory_file_path=str(memory_file),
            max_entries_per_type=100,
            memory_retention_days=30,
            auto_cleanup=True,
            backup_enabled=True
        )
        memory_manager = ProjectMetaMemoryManager(memory_config)
        print("✅ ProjectMetaMemoryManager initialized")

        # Simulate a complete project execution cycle
        print("\n🔄 Simulating project execution cycle...")
        
        project_id = "integrated_test_project"
        agent_id = "validator_agent"
        crew_id = "validator_crew"

        # Step 1: Check budget before execution
        print("\n💰 Step 1: Budget Check")
        budget_result = await budget_manager.check_budget(
            agent_id=agent_id,
            crew_id=crew_id,
            project_id=project_id,
            estimated_tokens=2000,
            model="gpt-4-turbo-preview"
        )
        print(f"   Budget check: {budget_result['reason']}")

        # Step 2: Simulate agent output
        print("\n🤖 Step 2: Agent Output Generation")
        agent_output = {
            "idea": "AI-powered task management app",
            "recommendation": "Proceed with development",
            "confidence_score": 0.85,
            "market_size": "$2.5B",
            "target_audience": "Remote teams"
        }

        # Step 3: Validate output
        print("\n🔍 Step 3: Output Validation")
        is_valid, validation_issues = output_validator.validate_output(
            agent_output, 
            "validation_result"
        )
        print(f"   Output valid: {is_valid}")
        print(f"   Validation issues: {len(validation_issues)}")
        
        for issue in validation_issues:
            print(f"     - {issue.severity}: {issue.message}")

        # Step 4: Record token usage
        print("\n📊 Step 4: Token Usage Recording")
        await budget_manager.record_usage(
            agent_id=agent_id,
            crew_id=crew_id,
            project_id=project_id,
            tokens_used=1800,
            model="gpt-4-turbo-preview"
        )
        print("   Token usage recorded")

        # Step 5: Store success pattern in memory
        print("\n🧠 Step 5: Memory Learning")
        if is_valid and len(validation_issues) == 0:
            # Store success pattern
            success_pattern = {
                "task_type": "market_validation",
                "approach": "comprehensive_analysis",
                "output_quality": "high",
                "token_efficiency": 0.9
            }
            
            memory_id = memory_manager.add_success_pattern(
                pattern=success_pattern,
                project_id=project_id,
                agent_id=agent_id,
                confidence_score=0.85
            )
            print(f"   Success pattern stored: {memory_id}")
        else:
            # Store failure pattern
            failure_pattern = {
                "task_type": "market_validation",
                "issues": [issue.message for issue in validation_issues],
                "output_quality": "low"
            }
            
            memory_id = memory_manager.add_failure_pattern(
                pattern=failure_pattern,
                project_id=project_id,
                agent_id=agent_id,
                error_type="validation_failed",
                confidence_score=0.7
            )
            print(f"   Failure pattern stored: {memory_id}")

        # Step 6: Get usage summary
        print("\n📈 Step 6: Usage Summary")
        usage_summary = await budget_manager.get_usage_summary(
            project_id=project_id
        )
        print(f"   Total tokens: {usage_summary['total_tokens']}")
        print(f"   Total cost: ${usage_summary['total_cost']:.4f}")

        # Step 7: Retrieve relevant patterns for next execution
        print("\n🔍 Step 7: Pattern Retrieval")
        patterns = memory_manager.get_relevant_patterns(
            agent_id=agent_id,
            context={"task_type": "market_validation"},
            pattern_type="both"
        )
        
        for pattern_type, entries in patterns.items():
            print(f"   {pattern_type} patterns: {len(entries)}")
            for entry in entries:
                print(f"     - {entry.content.get('context', 'N/A')} (confidence: {entry.confidence_score})")

        # Step 8: Test budget exceeded scenario
        print("\n⚠️  Step 8: Budget Exceeded Test")
        budget_result = await budget_manager.check_budget(
            agent_id=agent_id,
            crew_id=crew_id,
            project_id=project_id,
            estimated_tokens=4000,  # This should exceed per-agent limit
            model="gpt-4-turbo-preview"
        )
        print(f"   Budget check: {budget_result['reason']}")

        # Step 9: Test invalid output
        print("\n❌ Step 9: Invalid Output Test")
        invalid_output = {
            "idea": "AI-powered task management app"
            # Missing required fields
        }
        
        is_valid, issues = output_validator.validate_output(
            invalid_output, 
            "validation_result"
        )
        print(f"   Output valid: {is_valid}")
        print(f"   Issues found: {len(issues)}")
        for issue in issues:
            print(f"     - {issue.severity}: {issue.message}")

        # Step 10: Final statistics
        print("\n📊 Step 10: Final Statistics")
        
        # Budget stats
        budget_summary = await budget_manager.get_usage_summary(project_id=project_id)
        print(f"   Budget - Total tokens: {budget_summary['total_tokens']}, Cost: ${budget_summary['total_cost']:.4f}")
        
        # Memory stats
        memory_stats = memory_manager.get_memory_stats()
        print(f"   Memory - Total entries: {memory_stats['total_entries']}, Types: {len(memory_stats['type_counts'])}")
        
        # Validation stats
        validation_summary = output_validator.get_validation_summary(issues)
        print(f"   Validation - Issues: {validation_summary['total_issues']}, Confidence: {validation_summary['overall_confidence']:.2f}")

        print("\n🎉 Integrated core components test completed successfully!")

    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(test_integrated_core()) 