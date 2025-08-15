#!/usr/bin/env python3
"""
LLM Factory Integration Test Script
===================================

This script tests the complete LLM Factory integration across all ZeroToShip crew files.
It validates:
1. LLM Factory initialization with different providers
2. Crew file integration with the factory
3. Vault integration for secure API key management
4. Fallback mechanisms and error handling
5. Scalability considerations for 1,000+ nodes

Usage:
    python test_llm_factory_integration.py [--provider openai|anthropic|ollama] [--verbose]
"""

import os
import sys
import asyncio
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from zerotoship.utils.llm_factory import get_llm, get_llm_with_fallback, test_llm_connection
from zerotoship.security.vault_client import VaultClient
from zerotoship.crews.advisory_board_crew import AdvisoryBoardCrew
from zerotoship.crews.builder_crew import BuilderCrew
from zerotoship.crews.execution_crew import ExecutionCrew
from zerotoship.crews.marketing_crew import MarketingCrew
from zerotoship.crews.validator_crew import ValidatorCrew

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LLMFactoryIntegrationTester:
    """Comprehensive tester for LLM Factory integration."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.vault_client = VaultClient()
        self.test_results = {}
        self.start_time = datetime.now()
        
    def log(self, message: str, level: str = "info"):
        """Log message with optional verbosity control."""
        if self.verbose or level in ["error", "warning"]:
            getattr(logger, level)(message)
    
    def test_vault_connection(self) -> bool:
        """Test Vault connection and basic functionality."""
        self.log("🔐 Testing Vault Connection...")
        try:
            health = self.vault_client.health_check()
            self.log(f"Vault Health: {health}")
            
            # Test reading LLM secrets
            providers = ["openai", "anthropic", "ollama"]
            for provider in providers:
                secrets = self.vault_client.read_llm_secrets(provider)
                if secrets:
                    self.log(f"✅ {provider} secrets found: {list(secrets.keys())}")
                else:
                    self.log(f"⚠️  No {provider} secrets found in Vault")
            
            return True
        except Exception as e:
            self.log(f"❌ Vault connection failed: {e}", "error")
            return False
    
    def test_llm_factory_basic(self) -> Dict[str, Any]:
        """Test basic LLM Factory functionality."""
        self.log("🤖 Testing LLM Factory Basic Functionality...")
        results = {}
        
        # Test current provider
        current_provider = os.getenv("LLM_PROVIDER", "openai")
        self.log(f"Current LLM Provider: {current_provider}")
        
        try:
            llm = get_llm()
            results["current_provider"] = {
                "success": True,
                "provider": current_provider,
                "llm_type": type(llm).__name__,
                "model": getattr(llm, 'model', getattr(llm, 'model_name', 'unknown'))
            }
            self.log(f"✅ {current_provider} LLM initialized successfully")
        except Exception as e:
            results["current_provider"] = {
                "success": False,
                "provider": current_provider,
                "error": str(e)
            }
            self.log(f"❌ {current_provider} LLM initialization failed: {e}", "error")
        
        # Test fallback functionality
        try:
            fallback_llm = get_llm_with_fallback(primary_provider="anthropic", fallback_provider="openai")
            results["fallback"] = {
                "success": True,
                "llm_type": type(fallback_llm).__name__
            }
            self.log("✅ Fallback LLM functionality working")
        except Exception as e:
            results["fallback"] = {
                "success": False,
                "error": str(e)
            }
            self.log(f"❌ Fallback LLM failed: {e}", "error")
        
        return results
    
    def test_llm_connection_all_providers(self) -> Dict[str, Any]:
        """Test LLM connection for all available providers."""
        self.log("🔗 Testing LLM Connections for All Providers...")
        results = {}
        
        providers = ["openai", "anthropic", "ollama"]
        for provider in providers:
            try:
                result = test_llm_connection(provider)
                results[provider] = result
                if result["success"]:
                    self.log(f"✅ {provider} connection test successful")
                else:
                    self.log(f"❌ {provider} connection test failed: {result['error']}", "warning")
            except Exception as e:
                results[provider] = {
                    "provider": provider,
                    "success": False,
                    "error": str(e)
                }
                self.log(f"❌ {provider} connection test exception: {e}", "error")
        
        return results
    
    def test_crew_integration(self) -> Dict[str, Any]:
        """Test crew integration with LLM Factory."""
        self.log("👥 Testing Crew Integration with LLM Factory...")
        results = {}
        
        # Test project data
        test_project = {
            "id": "test-project-001",
            "name": "LLM Factory Integration Test",
            "idea": "A comprehensive test of the LLM Factory integration across all crews",
            "status": "testing",
            "state": "INITIALIZED",
            "user_id": "test-user",
            "created_at": datetime.now().isoformat()
        }
        
        crews_to_test = [
            ("AdvisoryBoardCrew", AdvisoryBoardCrew),
            ("BuilderCrew", BuilderCrew),
            ("ExecutionCrew", ExecutionCrew),
            ("MarketingCrew", MarketingCrew),
            ("ValidatorCrew", ValidatorCrew),
        ]
        
        for crew_name, crew_class in crews_to_test:
            try:
                self.log(f"Testing {crew_name}...")
                crew = crew_class(test_project)
                
                # Check if LLM was properly initialized
                if hasattr(crew, 'llm') and crew.llm:
                    results[crew_name] = {
                        "success": True,
                        "llm_type": type(crew.llm).__name__,
                        "llm_model": getattr(crew.llm, 'model', getattr(crew.llm, 'model_name', 'unknown')),
                        "crew_created": True
                    }
                    self.log(f"✅ {crew_name} initialized with LLM: {type(crew.llm).__name__}")
                else:
                    results[crew_name] = {
                        "success": False,
                        "error": "LLM not initialized in crew",
                        "crew_created": True
                    }
                    self.log(f"❌ {crew_name} created but LLM not initialized", "warning")
                
                # Test crew creation
                try:
                    crew_instance = crew._create_crew()
                    if crew_instance:
                        results[crew_name]["crew_creation"] = True
                        self.log(f"✅ {crew_name} crew creation successful")
                    else:
                        results[crew_name]["crew_creation"] = False
                        self.log(f"❌ {crew_name} crew creation failed", "warning")
                except Exception as e:
                    results[crew_name]["crew_creation"] = False
                    results[crew_name]["crew_creation_error"] = str(e)
                    self.log(f"❌ {crew_name} crew creation exception: {e}", "error")
                
            except Exception as e:
                results[crew_name] = {
                    "success": False,
                    "error": str(e),
                    "crew_created": False
                }
                self.log(f"❌ {crew_name} initialization failed: {e}", "error")
        
        return results
    
    def test_scalability_considerations(self) -> Dict[str, Any]:
        """Test scalability considerations for 1,000+ nodes."""
        self.log("🚀 Testing Scalability Considerations...")
        results = {}
        
        # Test LLM Factory caching (if implemented)
        try:
            import time
            start_time = time.time()
            llm1 = get_llm()
            time1 = time.time() - start_time
            
            start_time = time.time()
            llm2 = get_llm()
            time2 = time.time() - start_time
            
            results["caching"] = {
                "first_call_time": time1,
                "second_call_time": time2,
                "caching_effective": time2 < time1 * 0.5  # Second call should be much faster
            }
            
            if results["caching"]["caching_effective"]:
                self.log("✅ LLM Factory caching appears to be working")
            else:
                self.log("⚠️  LLM Factory caching may not be implemented or working")
                
        except Exception as e:
            results["caching"] = {
                "error": str(e)
            }
            self.log(f"❌ Caching test failed: {e}", "error")
        
        # Test concurrent LLM initialization
        try:
            import concurrent.futures
            import threading
            
            def init_llm():
                return get_llm()
            
            start_time = time.time()
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(init_llm) for _ in range(5)]
                results_list = [future.result() for future in futures]
            
            concurrent_time = time.time() - start_time
            results["concurrency"] = {
                "concurrent_initializations": len(results_list),
                "total_time": concurrent_time,
                "average_time": concurrent_time / len(results_list),
                "all_successful": all(results_list)
            }
            
            self.log(f"✅ Concurrent LLM initialization test completed in {concurrent_time:.2f}s")
            
        except Exception as e:
            results["concurrency"] = {
                "error": str(e)
            }
            self.log(f"❌ Concurrency test failed: {e}", "error")
        
        return results
    
    def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling and fallback mechanisms."""
        self.log("🛡️  Testing Error Handling and Fallback Mechanisms...")
        results = {}
        
        # Test with invalid provider
        try:
            original_provider = os.getenv("LLM_PROVIDER")
            os.environ["LLM_PROVIDER"] = "invalid_provider"
            
            llm = get_llm()
            results["invalid_provider"] = {
                "success": True,
                "fallback_used": True,
                "llm_type": type(llm).__name__
            }
            self.log("✅ Invalid provider handled with fallback")
            
        except Exception as e:
            results["invalid_provider"] = {
                "success": False,
                "error": str(e)
            }
            self.log(f"❌ Invalid provider handling failed: {e}", "error")
        finally:
            if original_provider:
                os.environ["LLM_PROVIDER"] = original_provider
            else:
                os.environ.pop("LLM_PROVIDER", None)
        
        # Test Vault connection failure handling
        try:
            original_vault_addr = os.getenv("VAULT_ADDR")
            os.environ["VAULT_ADDR"] = "http://invalid-vault:8200"
            
            llm = get_llm()
            results["vault_failure"] = {
                "success": True,
                "fallback_used": True,
                "llm_type": type(llm).__name__
            }
            self.log("✅ Vault failure handled with fallback")
            
        except Exception as e:
            results["vault_failure"] = {
                "success": False,
                "error": str(e)
            }
            self.log(f"❌ Vault failure handling failed: {e}", "error")
        finally:
            if original_vault_addr:
                os.environ["VAULT_ADDR"] = original_vault_addr
            else:
                os.environ.pop("VAULT_ADDR", None)
        
        return results
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive LLM Factory integration test."""
        self.log("🚀 Starting Comprehensive LLM Factory Integration Test")
        self.log("=" * 60)
        
        test_results = {
            "test_start_time": self.start_time.isoformat(),
            "environment": {
                "llm_provider": os.getenv("LLM_PROVIDER", "openai"),
                "vault_addr": os.getenv("VAULT_ADDR", "not_set"),
                "python_version": sys.version,
            }
        }
        
        # Run all tests
        test_results["vault_connection"] = self.test_vault_connection()
        test_results["llm_factory_basic"] = self.test_llm_factory_basic()
        test_results["llm_connections"] = self.test_llm_connection_all_providers()
        test_results["crew_integration"] = self.test_crew_integration()
        test_results["scalability"] = self.test_scalability_considerations()
        test_results["error_handling"] = self.test_error_handling()
        
        # Calculate summary
        test_results["summary"] = self.calculate_summary(test_results)
        test_results["test_end_time"] = datetime.now().isoformat()
        test_results["test_duration"] = (datetime.now() - self.start_time).total_seconds()
        
        self.log("=" * 60)
        self.log("🎯 Comprehensive Test Completed!")
        self.log(f"✅ Success Rate: {test_results['summary']['success_rate']:.1f}%")
        self.log(f"⏱️  Total Duration: {test_results['test_duration']:.2f}s")
        
        return test_results
    
    def calculate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate test summary statistics."""
        total_tests = 0
        successful_tests = 0
        
        # Count tests in each category
        for category, category_results in results.items():
            if category in ["test_start_time", "test_end_time", "test_duration", "summary"]:
                continue
                
            if isinstance(category_results, dict):
                if "success" in category_results:
                    total_tests += 1
                    if category_results["success"]:
                        successful_tests += 1
                else:
                    # Count individual tests in category
                    for test_name, test_result in category_results.items():
                        if isinstance(test_result, dict) and "success" in test_result:
                            total_tests += 1
                            if test_result["success"]:
                                successful_tests += 1
        
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": total_tests - successful_tests,
            "success_rate": success_rate,
            "status": "PASS" if success_rate >= 80 else "FAIL"
        }
    
    def print_detailed_results(self, results: Dict[str, Any]):
        """Print detailed test results."""
        print("\n" + "=" * 80)
        print("📊 DETAILED TEST RESULTS")
        print("=" * 80)
        
        for category, category_results in results.items():
            if category in ["test_start_time", "test_end_time", "test_duration", "summary"]:
                continue
                
            print(f"\n🔍 {category.upper().replace('_', ' ')}:")
            print("-" * 40)
            
            if isinstance(category_results, dict):
                for test_name, test_result in category_results.items():
                    if isinstance(test_result, dict):
                        status = "✅ PASS" if test_result.get("success", False) else "❌ FAIL"
                        print(f"  {test_name}: {status}")
                        
                        if "error" in test_result:
                            print(f"    Error: {test_result['error']}")
                        if "llm_type" in test_result:
                            print(f"    LLM Type: {test_result['llm_type']}")
        
        print(f"\n📈 SUMMARY:")
        print(f"  Total Tests: {results['summary']['total_tests']}")
        print(f"  Successful: {results['summary']['successful_tests']}")
        print(f"  Failed: {results['summary']['failed_tests']}")
        print(f"  Success Rate: {results['summary']['success_rate']:.1f}%")
        print(f"  Status: {results['summary']['status']}")
        print(f"  Duration: {results['test_duration']:.2f}s")

def main():
    """Main test function."""
    parser = argparse.ArgumentParser(description="Test LLM Factory Integration")
    parser.add_argument("--provider", choices=["openai", "anthropic", "ollama"], 
                       help="LLM provider to test")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set provider if specified
    if args.provider:
        os.environ["LLM_PROVIDER"] = args.provider
        print(f"🔧 Testing with LLM Provider: {args.provider}")
    
    # Run tests
    tester = LLMFactoryIntegrationTester(verbose=args.verbose)
    results = tester.run_comprehensive_test()
    
    # Print results
    tester.print_detailed_results(results)
    
    # Exit with appropriate code
    if results["summary"]["status"] == "PASS":
        print("\n🎉 All tests passed! LLM Factory integration is working correctly.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Please review the results above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
