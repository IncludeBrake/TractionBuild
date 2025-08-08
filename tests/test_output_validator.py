"""
Test script for OutputValidator functionality.
"""

import asyncio
from src.zerotoship.core.output_validator import OutputValidator, OutputValidatorConfig, ValidationSeverity


async def test_output_validator():
    """Test the output validator functionality."""

    # Initialize output validator
    config = OutputValidatorConfig(
        enable_hallucination_detection=True,
        enable_security_checks=True,
        enable_format_validation=True,
        max_content_length=1000
    )
    
    validator = OutputValidator(config)

    print("🔍 Testing OutputValidator...")

    # Test 1: Valid output
    valid_output = {
        "idea": "AI-powered task management app",
        "recommendation": "Proceed with development",
        "confidence_score": 0.85
    }
    
    is_valid, issues = validator.validate_output(valid_output, "validation_result")
    print(f"✅ Valid output test: {is_valid}, {len(issues)} issues")
    if issues:
        for issue in issues:
            print(f"   - {issue.severity}: {issue.message}")

    # Test 2: Invalid output (missing required fields)
    invalid_output = {
        "idea": "AI-powered task management app"
        # Missing recommendation and confidence_score
    }
    
    is_valid, issues = validator.validate_output(invalid_output, "validation_result")
    print(f"❌ Invalid output test: {is_valid}, {len(issues)} issues")
    for issue in issues:
        print(f"   - {issue.severity}: {issue.message}")

    # Test 3: Hallucination detection
    hallucination_output = "I apologize, but I cannot provide specific information about this topic. As an AI language model, I don't have access to real-time data."
    
    is_valid, issues = validator.validate_output(hallucination_output, "general")
    print(f"🤖 Hallucination test: {is_valid}, {len(issues)} issues")
    for issue in issues:
        if issue.rule.value == "hallucination_detection":
            print(f"   - {issue.severity}: {issue.message}")

    # Test 4: Security check
    security_output = "Here's some code: <script>alert('xss')</script> and eval('dangerous')"
    
    is_valid, issues = validator.validate_output(security_output, "general")
    print(f"🔒 Security test: {is_valid}, {len(issues)} issues")
    for issue in issues:
        if issue.rule.value == "security_check":
            print(f"   - {issue.severity}: {issue.message}")

    # Test 5: Placeholder content
    placeholder_output = "This is a TODO item that needs to be completed. It's just a PLACEHOLDER for now."
    
    is_valid, issues = validator.validate_output(placeholder_output, "general")
    print(f"📝 Placeholder test: {is_valid}, {len(issues)} issues")
    for issue in issues:
        if issue.rule.value == "content_validity":
            print(f"   - {issue.severity}: {issue.message}")

    # Test 6: Repetitive content
    repetitive_output = "This is a test. This is a test. This is a test. This is a test. This is a test."
    
    is_valid, issues = validator.validate_output(repetitive_output, "general")
    print(f"🔄 Repetitive content test: {is_valid}, {len(issues)} issues")
    for issue in issues:
        if issue.rule.value == "content_validity":
            print(f"   - {issue.severity}: {issue.message}")

    # Test 7: Unrealistic confidence score
    unrealistic_output = {
        "idea": "AI-powered task management app",
        "recommendation": "Proceed with development",
        "confidence_score": 0.999  # Unrealistically high
    }
    
    is_valid, issues = validator.validate_output(unrealistic_output, "validation_result")
    print(f"📊 Unrealistic confidence test: {is_valid}, {len(issues)} issues")
    for issue in issues:
        if issue.rule.value == "content_validity":
            print(f"   - {issue.severity}: {issue.message}")

    # Test 8: Get validation summary
    summary = validator.get_validation_summary(issues)
    print(f"📋 Validation summary: {summary}")

    print("🎉 Output validator tests completed!")


if __name__ == "__main__":
    asyncio.run(test_output_validator()) 