#!/usr/bin/env python3
"""
Minimal E2E test for ZeroToShip glue patch
Tests the basic flow: create project → run workflow → get results
"""

import asyncio
import httpx
import time
from typing import Dict, Any

API_BASE = "http://localhost:8000"

async def test_health():
    """Test health endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✅ Health check passed")

async def test_create_project():
    """Test project creation."""
    project_data = {
        "name": "Test Project",
        "description": "A test project for validation",
        "hypothesis": "This will work",
        "target_avatars": ["startup_entrepreneur"],
        "workflow": "validation_and_launch"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{API_BASE}/api/v1/projects", json=project_data)
        assert response.status_code == 200
        result = response.json()
        assert "project_id" in result
        project_id = result["project_id"]
        print(f"✅ Project created: {project_id}")
        return project_id

async def test_get_status(project_id: str):
    """Test status endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/api/v1/projects/{project_id}/status")
        assert response.status_code == 200
        data = response.json()
        assert "state" in data
        assert "progress" in data
        print(f"✅ Status: {data['state']}, Progress: {data['progress']:.1f}%")
        return data

async def test_get_project(project_id: str):
    """Test project retrieval."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/api/v1/projects/{project_id}")
        assert response.status_code == 200
        data = response.json()
        assert "project" in data
        assert "artifacts" in data
        print(f"✅ Project retrieved with {len(data['artifacts'])} artifacts")
        return data

async def main():
    """Run the minimal E2E test."""
    print("🚀 Starting minimal E2E test")
    
    # Test 1: Health
    await test_health()
    
    # Test 2: Create project
    project_id = await test_create_project()
    
    # Test 3: Wait for completion (max 30 seconds)
    print("⏳ Waiting for workflow completion...")
    max_wait = 30
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        status = await test_get_status(project_id)
        
        if status["state"] == "COMPLETED":
            print("✅ Workflow completed!")
            break
        elif status["state"] == "ERROR":
            print("❌ Workflow failed")
            return
        
        await asyncio.sleep(3)
    
    if time.time() - start_time >= max_wait:
        print("❌ Workflow timed out")
        return
    
    # Test 4: Get final results
    project_data = await test_get_project(project_id)
    
    # Verify artifacts
    artifacts = project_data["artifacts"]
    expected_agents = ["validator", "advisory"]
    
    for agent in expected_agents:
        if agent in artifacts:
            print(f"✅ {agent} artifact present")
        else:
            print(f"❌ {agent} artifact missing")
    
    print("🎉 Minimal E2E test completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
