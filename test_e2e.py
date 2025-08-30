#!/usr/bin/env python3
"""
E2E Test for ZeroToShip API
Tests the complete flow: create project → run workflow → get results
"""

import asyncio
import httpx
import time
import json
from typing import Dict, Any

API_BASE = "http://localhost:8000"

async def test_create_project() -> str:
    """Create a test project and return the project ID."""
    project_data = {
        "name": "Test SaaS Platform",
        "description": "A B2B SaaS platform for project management",
        "hypothesis": "Small businesses need better project management tools",
        "target_avatars": ["sme", "startup_entrepreneur"],
        "workflow": "validation_and_launch"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{API_BASE}/api/v1/projects", json=project_data)
        response.raise_for_status()
        result = response.json()
        return result["project_id"]

async def test_get_project_status(project_id: str) -> Dict[str, Any]:
    """Get project status."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/api/v1/projects/{project_id}/status")
        response.raise_for_status()
        return response.json()

async def test_get_project(project_id: str) -> Dict[str, Any]:
    """Get full project with artifacts."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/api/v1/projects/{project_id}")
        response.raise_for_status()
        return response.json()

async def test_health_check() -> bool:
    """Test health check endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/health")
        return response.status_code == 200

async def test_metrics() -> Dict[str, Any]:
    """Test metrics endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/metrics")
        response.raise_for_status()
        return response.json()

async def main():
    """Run the complete E2E test."""
    print("🚀 Starting ZeroToShip E2E Test")
    
    # Test 1: Health check
    print("\n1. Testing health check...")
    health_ok = await test_health_check()
    if health_ok:
        print("✅ Health check passed")
    else:
        print("❌ Health check failed")
        return
    
    # Test 2: Create project
    print("\n2. Creating test project...")
    try:
        project_id = await test_create_project()
        print(f"✅ Project created with ID: {project_id}")
    except Exception as e:
        print(f"❌ Failed to create project: {e}")
        return
    
    # Test 3: Wait for workflow completion
    print("\n3. Waiting for workflow completion...")
    max_wait = 60  # 60 seconds timeout
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            status = await test_get_project_status(project_id)
            print(f"   Status: {status['state']}, Progress: {status['progress']:.1f}%")
            
            if status['state'] == 'COMPLETED':
                print("✅ Workflow completed successfully")
                break
            elif status['state'] == 'ERROR':
                print("❌ Workflow failed")
                return
                
            await asyncio.sleep(5)  # Wait 5 seconds before checking again
            
        except Exception as e:
            print(f"❌ Error checking status: {e}")
            return
    
    if time.time() - start_time >= max_wait:
        print("❌ Workflow timed out")
        return
    
    # Test 4: Get final results
    print("\n4. Getting final results...")
    try:
        project_data = await test_get_project(project_id)
        print(f"✅ Project retrieved successfully")
        print(f"   Artifacts: {len(project_data['artifacts'])}")
        print(f"   Logs: {len(project_data['logs'])}")
        
        # Print artifact types
        for artifact in project_data['artifacts']:
            print(f"   - {artifact['type']}")
            
    except Exception as e:
        print(f"❌ Failed to get project: {e}")
        return
    
    # Test 5: Check metrics
    print("\n5. Checking metrics...")
    try:
        metrics = await test_metrics()
        print(f"✅ Metrics retrieved")
        print(f"   Total requests: {metrics.get('zerotoship_requests_total', 0)}")
        print(f"   Projects created: {metrics.get('zerotoship_projects_created', 0)}")
        print(f"   Projects retrieved: {metrics.get('zerotoship_projects_retrieved', 0)}")
        
    except Exception as e:
        print(f"❌ Failed to get metrics: {e}")
    
    print("\n🎉 E2E Test completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
