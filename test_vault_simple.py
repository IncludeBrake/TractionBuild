#!/usr/bin/env python3
"""
Simple test script for Vault integration with LLM configuration.
This script tests the secure retrieval of LLM API keys from Vault.
"""

import os
import sys
import logging
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from zerotoship.security.vault_client import VaultClient
from zerotoship.utils.llm_config import LLMConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_vault_client():
    """Test the Vault client functionality."""
    print("🔐 Testing Vault Client...")
    
    vault = VaultClient()
    
    # Test Vault health
    health = vault.health_check()
    print(f"Vault Health: {health}")
    
    # Test LLM secrets reading
    print("\n📖 Testing LLM Secrets Reading...")
    
    # Test OpenAI secrets
    openai_secrets = vault.read_llm_secrets("openai")
    if openai_secrets:
        print(f"✅ OpenAI secrets found: {list(openai_secrets.keys())}")
    else:
        print("⚠️  No OpenAI secrets found in Vault")
    
    # Test Ollama secrets
    ollama_secrets = vault.read_llm_secrets("ollama")
    if ollama_secrets:
        print(f"✅ Ollama secrets found: {list(ollama_secrets.keys())}")
    else:
        print("⚠️  No Ollama secrets found in Vault")

def test_llm_config():
    """Test the LLM configuration functionality."""
    print("\n🤖 Testing LLM Configuration...")
    
    config = LLMConfig()
    
    # Test OpenAI LLM configuration
    print("\n🔧 Testing OpenAI LLM Configuration...")
    openai_llm = config.get_openai_llm()
    if openai_llm:
        print("✅ OpenAI LLM configured successfully")
        print(f"   Model: {openai_llm.model_name}")
    else:
        print("❌ OpenAI LLM configuration failed")
    
    # Test Ollama LLM configuration
    print("\n🔧 Testing Ollama LLM Configuration...")
    ollama_llm = config.get_ollama_llm()
    if ollama_llm:
        print("✅ Ollama LLM configured successfully")
        print(f"   Model: {ollama_llm.model}")
        print(f"   Base URL: {ollama_llm.base_url}")
    else:
        print("❌ Ollama LLM configuration failed")
    
    # Test hybrid LLM configuration
    print("\n🔧 Testing Hybrid LLM Configuration...")
    hybrid_llm = config.get_hybrid_llm(primary_provider="openai", fallback_provider="ollama")
    if hybrid_llm:
        print("✅ Hybrid LLM configured successfully")
        if hasattr(hybrid_llm, 'model_name'):
            print(f"   Using: OpenAI ({hybrid_llm.model_name})")
        elif hasattr(hybrid_llm, 'model'):
            print(f"   Using: Ollama ({hybrid_llm.model})")
    else:
        print("❌ Hybrid LLM configuration failed")

def test_crew_integration():
    """Test crew integration with Vault-based LLM configuration."""
    print("\n👥 Testing Crew Integration...")
    
    try:
        from zerotoship.crews.advisory_board_crew import AdvisoryBoardCrew
        
        # Create a test project
        test_project = {
            "id": "test-project-001",
            "name": "Test Project",
            "idea": "A test idea for validation",
            "status": "initialized"
        }
        
        # Initialize the crew
        crew = AdvisoryBoardCrew(test_project)
        print("✅ Advisory Board Crew initialized successfully")
        
        # Test crew creation
        crew_instance = crew._create_crew()
        if crew_instance:
            print("✅ Crew creation successful")
            print(f"   Agents: {len(crew_instance.agents)}")
            print(f"   Tasks: {len(crew_instance.tasks)}")
        else:
            print("❌ Crew creation failed")
            
    except Exception as e:
        print(f"❌ Crew integration test failed: {e}")

def main():
    """Main test function."""
    print("🚀 Starting Vault Integration Tests...")
    print("=" * 50)
    
    try:
        # Test Vault client
        test_vault_client()
        
        # Test LLM configuration
        test_llm_config()
        
        # Test crew integration
        test_crew_integration()
        
        print("\n" + "=" * 50)
        print("✅ Vault integration tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
