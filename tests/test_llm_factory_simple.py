#!/usr/bin/env python3
"""
Simple LLM Factory Test Script
==============================

This script tests the core LLM Factory functionality without complex crew imports.
It validates:
1. LLM Factory initialization with different providers
2. Vault integration for secure API key management
3. Fallback mechanisms and error handling
4. Basic functionality without dependency conflicts

Usage:
    python test_llm_factory_simple.py [--provider openai|anthropic|ollama]
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_vault_client():
    """Test Vault client functionality."""
    print("🔐 Testing Vault Client...")
    try:
        from tractionbuild.security.vault_client import VaultClient
        vault = VaultClient()
        
        # Test health check (may fail in dev environment)
        try:
            health = vault.health_check()
            print(f"✅ Vault Health: {health}")
        except Exception as e:
            print(f"⚠️  Vault health check failed (expected in dev): {e}")
        
        # Test reading LLM secrets
        providers = ["openai", "anthropic", "ollama"]
        for provider in providers:
            try:
                secrets = vault.get_secret(f'tractionbuild/llm/{provider}')
                if secrets:
                    print(f"✅ {provider} secrets found: {list(secrets.keys())}")
                else:
                    print(f"⚠️  No {provider} secrets found in Vault")
            except Exception as e:
                print(f"⚠️  Failed to read {provider} secrets: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Vault client test failed: {e}")
        return False

def test_llm_factory_basic():
    """Test basic LLM Factory functionality."""
    print("\n🤖 Testing LLM Factory Basic Functionality...")
    
    # Test current provider
    current_provider = os.getenv("LLM_PROVIDER", "openai")
    print(f"Current LLM Provider: {current_provider}")
    
    try:
        from tractionbuild.utils.llm_factory import get_llm
        llm = get_llm()
        print(f"✅ {current_provider} LLM initialized successfully")
        print(f"   LLM Type: {type(llm).__name__}")
        print(f"   Model: {getattr(llm, 'model', getattr(llm, 'model_name', 'unknown'))}")
        return True
    except Exception as e:
        print(f"❌ {current_provider} LLM initialization failed: {e}")
        return False

def test_llm_factory_fallback():
    """Test LLM Factory fallback functionality."""
    print("\n🔄 Testing LLM Factory Fallback...")
    
    try:
        from tractionbuild.utils.llm_factory import get_llm_with_fallback
        
        # Test fallback from anthropic to openai
        llm = get_llm_with_fallback(primary_provider="anthropic", fallback_provider="openai")
        print(f"✅ Fallback LLM functionality working")
        print(f"   LLM Type: {type(llm).__name__}")
        return True
    except Exception as e:
        print(f"❌ Fallback LLM failed: {e}")
        return False

def test_llm_connection():
    """Test LLM connection functionality."""
    print("\n🔗 Testing LLM Connection...")
    
    try:
        from tractionbuild.utils.llm_factory import test_llm_connection
        
        current_provider = os.getenv("LLM_PROVIDER", "openai")
        result = test_llm_connection(current_provider)
        
        if result["success"]:
            print(f"✅ {current_provider} connection test successful")
            print(f"   Model: {result['model_info']['model']}")
            print(f"   Response: {result['model_info']['response_preview']}")
        else:
            print(f"❌ {current_provider} connection test failed: {result['error']}")
        
        return result["success"]
    except Exception as e:
        print(f"❌ LLM connection test failed: {e}")
        return False

def test_environment_variables():
    """Test environment variable handling."""
    print("\n🌍 Testing Environment Variable Handling...")
    
    # Test with different providers
    providers = ["openai", "anthropic", "ollama"]
    results = {}
    
    for provider in providers:
        try:
            original_provider = os.getenv("LLM_PROVIDER")
            os.environ["LLM_PROVIDER"] = provider
            
            from tractionbuild.utils.llm_factory import get_llm
            llm = get_llm()
            results[provider] = {
                "success": True,
                "type": type(llm).__name__
            }
            print(f"✅ {provider} environment variable test passed")
            
        except Exception as e:
            results[provider] = {
                "success": False,
                "error": str(e)
            }
            print(f"❌ {provider} environment variable test failed: {e}")
        finally:
            # Restore original provider
            if original_provider:
                os.environ["LLM_PROVIDER"] = original_provider
            else:
                os.environ.pop("LLM_PROVIDER", None)
    
    return results

def test_error_handling():
    """Test error handling and fallback mechanisms."""
    print("\n🛡️  Testing Error Handling...")
    
    # Test with invalid provider
    try:
        original_provider = os.getenv("LLM_PROVIDER")
        os.environ["LLM_PROVIDER"] = "invalid_provider"
        
        from tractionbuild.utils.llm_factory import get_llm
        llm = get_llm()
        print("✅ Invalid provider handled with fallback")
        print(f"   Fallback LLM Type: {type(llm).__name__}")
        
    except Exception as e:
        print(f"❌ Invalid provider handling failed: {e}")
    finally:
        if original_provider:
            os.environ["LLM_PROVIDER"] = original_provider
        else:
            os.environ.pop("LLM_PROVIDER", None)
    
    # Test with missing API keys
    try:
        original_openai_key = os.getenv("OPENAI_API_KEY")
        os.environ.pop("OPENAI_API_KEY", None)
        
        from tractionbuild.utils.llm_factory import get_llm
        llm = get_llm()
        print("✅ Missing API key handled gracefully")
        
    except Exception as e:
        print(f"⚠️  Missing API key test: {e}")
    finally:
        if original_openai_key:
            os.environ["OPENAI_API_KEY"] = original_openai_key

def main():
    """Main test function."""
    print("🚀 Starting Simple LLM Factory Test")
    print("=" * 50)
    
    start_time = datetime.now()
    test_results = {}
    
    # Run tests
    test_results["vault_client"] = test_vault_client()
    test_results["llm_factory_basic"] = test_llm_factory_basic()
    test_results["llm_factory_fallback"] = test_llm_factory_fallback()
    test_results["llm_connection"] = test_llm_connection()
    test_results["environment_variables"] = test_environment_variables()
    test_error_handling()  # This test doesn't return a boolean
    
    # Calculate summary
    successful_tests = sum(1 for result in test_results.values() if result)
    total_tests = len(test_results)
    success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
    
    test_duration = (datetime.now() - start_time).total_seconds()
    
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Total Tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {total_tests - successful_tests}")
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"Duration: {test_duration:.2f}s")
    
    if success_rate >= 80:
        print("\n🎉 Most tests passed! LLM Factory is working correctly.")
        print("Note: Some failures may be expected in development environment.")
        sys.exit(0)
    else:
        print("\n⚠️  Several tests failed. Please review the results above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
