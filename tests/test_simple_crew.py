"""
Simple test for crew functionality.
"""

import asyncio
from src.tractionbuild.crews.validator_crew import ValidatorCrew, ValidatorCrewConfig


async def test_simple_crew():
    """Test basic crew functionality."""
    
    print("🚀 Testing Simple Crew Functionality...")
    
    # Initialize crew
    config = ValidatorCrewConfig(
        enable_memory_learning=True,
        enable_sequential_validation=True
    )
    crew = ValidatorCrew(config)
    
    print("✅ Crew initialized successfully")
    
    # Test basic functionality
    test_idea = "AI-powered task management app"
    
    try:
        # Test the validate_idea method
        result = await crew.validate_idea(
            idea=test_idea,
            context={"industry": "saas"}
        )
        
        print("✅ Validation completed successfully")
        print(f"   Idea: {result.idea}")
        print(f"   Market Size: {result.market_size}")
        print(f"   Recommendation: {result.recommendation}")
        print(f"   Confidence: {result.confidence_score}")
        
    except Exception as e:
        print(f"❌ Error during validation: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        
        # Test memory functionality
        try:
            memory_stats = crew.memory_manager.get_memory_stats()
            print(f"✅ Memory stats: {memory_stats['total_entries']} entries")
        except Exception as mem_error:
            print(f"❌ Memory error: {str(mem_error)}")
    
    print("🎉 Simple crew test completed!")


if __name__ == "__main__":
    asyncio.run(test_simple_crew()) 
