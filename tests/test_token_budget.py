"""
Test script for TokenBudgetManager functionality.
"""

import asyncio
from src.tractionbuild.core.token_budget import TokenBudgetManager, BudgetLevel, BudgetAction


async def test_token_budget():
    """Test the token budget manager functionality."""
    
    # Initialize token budget manager
    budget_manager = TokenBudgetManager(
        per_agent_limit=5000,
        per_crew_limit=20000,
        per_run_limit=50000,
        enable_budgeting=True,
        enable_cost_tracking=True
    )
    
    print("🧠 Testing TokenBudgetManager...")
    
    # Test 1: Check budget before any usage
    result = await budget_manager.check_budget(
        agent_id="validator_agent",
        crew_id="validator_crew", 
        project_id="test_project",
        estimated_tokens=1000,
        model="gpt-4o-mini"
    )
    print(f"✅ Budget check result: {result}")
    
    # Test 2: Record some usage
    await budget_manager.record_usage(
        agent_id="validator_agent",
        crew_id="validator_crew",
        project_id="test_project", 
        tokens_used=2000,
        model="gpt-4o-mini"
    )
    print("✅ Recorded 2000 tokens usage")
    
    # Test 3: Check budget after usage
    result = await budget_manager.check_budget(
        agent_id="validator_agent",
        crew_id="validator_crew",
        project_id="test_project",
        estimated_tokens=4000,  # This should exceed per-agent limit
        model="gpt-4o-mini"
    )
    print(f"⚠️  Budget check after usage: {result}")
    
    # Test 4: Get usage summary
    summary = await budget_manager.get_usage_summary(
        project_id="test_project"
    )
    print(f"📊 Usage summary: {summary}")
    
    # Test 5: Test throttling
    result = await budget_manager.check_budget(
        agent_id="validator_agent",
        crew_id="validator_crew", 
        project_id="test_project",
        estimated_tokens=10000,  # This should trigger throttling
        model="gpt-4o-mini"
    )
    print(f"🚦 Throttling test: {result}")
    
    print("🎉 Token budget tests completed!")


if __name__ == "__main__":
    asyncio.run(test_token_budget()) 
