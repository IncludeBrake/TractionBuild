#!/usr/bin/env python3
"""
Test script to verify AdvisoryBoardCrew functionality.
"""

import sys
import os
import asyncio

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_advisory_board():
    """Test the AdvisoryBoardCrew functionality."""
    try:
        from tractionbuild.crews import CREW_REGISTRY
        print("✅ Successfully imported CREW_REGISTRY")
        print(f"📋 Available crews: {list(CREW_REGISTRY.keys())}")
        
        if 'AdvisoryBoardCrew' in CREW_REGISTRY:
            print("✅ AdvisoryBoardCrew is registered!")
            
            # Test crew instantiation
            crew_class = CREW_REGISTRY['AdvisoryBoardCrew']
            project_data = {
                "idea": "I want to build an app that helps people manage their daily tasks",
                "user_id": "test_user_123",
                "session_id": "test_session"
            }
            
            crew = crew_class(project_data)
            print("✅ AdvisoryBoardCrew instantiated successfully!")
            print(f"📝 Crew class: {crew_class}")
            print(f"📝 Crew docstring: {crew_class.__doc__}")
            
            # Test crew creation
            crew_instance = crew._create_crew()
            print("✅ Crew creation successful!")
            print(f"📊 Number of agents: {len(crew_instance.agents)}")
            print(f"📊 Number of tasks: {len(crew_instance.tasks)}")
            
            # Test execution (optional - might take time)
            print("\n🔄 Testing crew execution...")
            try:
                result = await crew._execute_crew({"idea": "test idea", "context": {}})
                print("✅ Crew execution successful!")
                print(f"📋 Result keys: {list(result.keys())}")
                print(f"🎯 Mission statement: {result.get('mission_statement', 'Not found')}")
            except Exception as e:
                print(f"⚠️ Crew execution failed (this might be expected): {e}")
            
        else:
            print("❌ AdvisoryBoardCrew is NOT registered!")
            print("Available crews:", list(CREW_REGISTRY.keys()))
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_advisory_board())
