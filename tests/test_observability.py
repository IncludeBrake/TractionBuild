#!/usr/bin/env python3
"""
Test script for tractionbuild Observability Dashboard
==================================================

This script tests the observability crew and dashboard functionality.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tractionbuild.crews.observability_crew import ObservabilityCrew, ObservabilityMetrics
from tractionbuild.utils.llm_factory import get_llm

async def test_observability_crew():
    """Test the ObservabilityCrew functionality."""
    
    print("🧪 Testing ObservabilityCrew...")
    
    # Create test project data
    project_data = {
        "id": "test_project_123",
        "idea": "Test product idea for observability",
        "workflow": "default_software_build",
        "state": "IDEA_VALIDATION"
    }
    
    try:
        # Create observability crew
        crew = ObservabilityCrew(project_data)
        print("✅ ObservabilityCrew created successfully")
        
        # Test metrics collection
        metrics = await crew.collect_metrics()
        print(f"✅ Metrics collected: {metrics.model_dump()}")
        
        # Test anomaly detection
        anomalies = await crew.detect_anomalies(metrics)
        print(f"✅ Anomalies detected: {len(anomalies)}")
        for anomaly in anomalies:
            print(f"   - {anomaly['type']}: {anomaly['description']}")
        
        # Test recommendations
        recommendations = await crew.generate_recommendations(metrics, anomalies)
        print(f"✅ Recommendations generated: {len(recommendations)}")
        for rec in recommendations:
            print(f"   - {rec['title']}: {rec['description']}")
        
        # Test full analysis
        result = await crew.run_async(project_data)
        print(f"✅ Full analysis completed: {result.get('timestamp', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing ObservabilityCrew: {e}")
        return False

async def test_llm_factory():
    """Test the LLM factory."""
    
    print("🧪 Testing LLM Factory...")
    
    try:
        llm = get_llm()
        print("✅ LLM factory working")
        return True
    except Exception as e:
        print(f"❌ Error with LLM factory: {e}")
        return False

async def test_metrics_model():
    """Test the ObservabilityMetrics model."""
    
    print("🧪 Testing ObservabilityMetrics model...")
    
    try:
        metrics = ObservabilityMetrics(
            quality_score=0.85,
            cost_per_1k_tokens=0.002,
            drift_score=0.05,
            time_to_value=120.0,
            error_rate=0.03,
            carbon_footprint=0.5,
            compliance_score=0.95
        )
        
        print(f"✅ Metrics model created: {metrics.model_dump()}")
        return True
        
    except Exception as e:
        print(f"❌ Error with metrics model: {e}")
        return False

async def main():
    """Main test function."""
    
    print("🚀 tractionbuild Observability Test Suite")
    print("=" * 50)
    
    tests = [
        ("LLM Factory", test_llm_factory),
        ("Metrics Model", test_metrics_model),
        ("Observability Crew", test_observability_crew),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Observability system is ready.")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
