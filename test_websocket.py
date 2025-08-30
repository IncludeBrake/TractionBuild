#!/usr/bin/env python3
"""
Simple WebSocket test client for ZeroToShip
"""
import asyncio
import websockets
import json
import requests

async def test_websocket(project_id: str):
    """Test WebSocket connection and event streaming."""
    uri = f"ws://localhost:8000/ws/projects/{project_id}"
    
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected!")
            
            # Wait for events
            event_count = 0
            while event_count < 5:  # Expect ~5 events
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    event = json.loads(message)
                    event_count += 1
                    print(f"📡 Event {event_count}: {event['type']}")
                    
                    if event['type'] == 'status_update' and event.get('state') == 'COMPLETED':
                        print("🎉 Project completed!")
                        break
                        
                except asyncio.TimeoutError:
                    print("⏰ Timeout waiting for events")
                    break
                    
    except Exception as e:
        print(f"❌ WebSocket error: {e}")

def create_project():
    """Create a test project."""
    url = "http://localhost:8000/api/v1/projects"
    data = {
        "name": "websocket-test",
        "description": "Testing WebSocket events",
        "hypothesis": "Real-time event streaming works",
        "target_avatars": ["startup_entrepreneur"],
        "workflow": "validation_and_launch"
    }
    
    response = requests.post(url, json=data)
    if response.status_code == 200:
        project_id = response.json()["project_id"]
        print(f"✅ Project created: {project_id}")
        return project_id
    else:
        print(f"❌ Failed to create project: {response.text}")
        return None

async def main():
    """Main test function."""
    print("🚀 Testing ZeroToShip WebSocket Events")
    print("=" * 50)
    
    # Create a project
    project_id = create_project()
    if not project_id:
        return
    
    # Test WebSocket
    await test_websocket(project_id)
    
    print("=" * 50)
    print("✅ WebSocket test completed!")

if __name__ == "__main__":
    asyncio.run(main())
