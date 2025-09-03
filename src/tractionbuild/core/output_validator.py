"""
Output Validator for tractionbuild.
Validates agent outputs to catch hallucinations, bad formatting, and invalid content.
"""

import re
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from pydantic import BaseModel, Field, ValidationError


class ValidationSeverity(str, Enum):
    """Validation severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationRule(str, Enum):
    """Types of validation rules."""
    FORMAT_CHECK = "format_check"
    CONTENT_VALIDITY = "content_validity"
    HALLUCINATION_DETECTION = "hallucination_detection"
    CONSISTENCY_CHECK = "consistency_check"
    COMPLETENESS_CHECK = "completeness_check"
    SECURITY_CHECK = "security_check"


@dataclass
class ValidationIssue:
    """Validation issue details."""
    rule: ValidationRule
    severity: ValidationSeverity
    message: str
    field: Optional[str] = None
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    confidence: float = 0.0


class OutputValidatorConfig(BaseModel):
    """Configuration for the Output Validator."""
    
    enable_hallucination_detection: bool = Field(default=True, description="Enable hallucination detection")
    enable_security_checks: bool = Field(default=True, description="Enable security checks")
    enable_format_validation: bool = Field(default=True, description="Enable format validation")
    max_content_length: int = Field(default=50000, description="Maximum content length")
    min_confidence_threshold: float = Field(default=0.3, description="Minimum confidence threshold")
    suspicious_patterns: List[str] = Field(default_factory=list, description="Suspicious content patterns")
    required_fields: Dict[str, List[str]] = Field(default_factory=dict, description="Required fields by output type")


class OutputValidator:
    """Validates agent outputs for quality and safety."""
    
    def __init__(self, config: Optional[OutputValidatorConfig] = None):
        """Initialize the Output Validator."""
        self.config = config or OutputValidatorConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize suspicious patterns
        self._init_suspicious_patterns()
        
        # Initialize required fields
        self._init_required_fields()
    
    def _init_suspicious_patterns(self):
        """Initialize suspicious content patterns."""
        if not self.config.suspicious_patterns:
            self.config.suspicious_patterns = [
                r"I apologize, but I cannot",
                r"I don't have access to",
                r"I'm not able to",
                r"Unfortunately, I cannot",
                r"I'm sorry, but I",
                r"<script>",
                r"javascript:",
                r"eval\(",
                r"exec\(",
                r"import\s+os",
                r"subprocess\.",
                r"__import__\(",
                r"globals\(",
                r"locals\(",
                r"getattr\(",
                r"setattr\(",
                r"delattr\(",
                r"hasattr\(",
                r"vars\(",
                r"dir\(",
                r"type\(",
                r"isinstance\(",
                r"issubclass\(",
                r"super\(",
                r"property\(",
                r"staticmethod\(",
                r"classmethod\(",
                r"compile\(",
                r"eval\(",
                r"exec\(",
                r"repr\(",
                r"ascii\(",
                r"bin\(",
                r"chr\(",
                r"ord\(",
                r"hex\(",
                r"oct\(",
                r"format\(",
                r"frozenset\(",
                r"hash\(",
                r"id\(",
                r"input\(",
                r"iter\(",
                r"len\(",
                r"map\(",
                r"max\(",
                r"min\(",
                r"next\(",
                r"open\(",
                r"pow\(",
                r"print\(",
                r"range\(",
                r"reversed\(",
                r"round\(",
                r"set\(",
                r"sorted\(",
                r"sum\(",
                r"tuple\(",
                r"zip\(",
                r"abs\(",
                r"all\(",
                r"any\(",
                r"bool\(",
                r"callable\(",
                r"complex\(",
                r"divmod\(",
                r"enumerate\(",
                r"filter\(",
                r"float\(",
                r"int\(",
                r"list\(",
                r"object\(",
                r"slice\(",
                r"str\(",
                r"type\(",
            ]
    
    def _init_required_fields(self):
        """Initialize required fields for different output types."""
        if not self.config.required_fields:
            self.config.required_fields = {
                "validation_result": ["idea", "recommendation", "confidence_score"],
                "market_analysis": ["market_size", "competition_level", "target_audience"],
                "execution_plan": ["tasks", "timeline", "dependencies"],
                "code_output": ["code", "language", "description"],
                "marketing_content": ["headline", "copy", "target_audience"]
            }
    
    def validate_output(
        self, 
        output: Any, 
        output_type: str = "general",
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, List[ValidationIssue]]:
        """
        Validate agent output.
        
        Args:
            output: The output to validate
            output_type: Type of output for specific validation rules
            context: Additional context for validation
            
        Returns:
            Tuple of (is_valid, validation_issues)
        """
        issues = []
        
        # Basic format validation
        if self.config.enable_format_validation:
            format_issues = self._validate_format(output, output_type)
            issues.extend(format_issues)
        
        # Content validity checks
        validity_issues = self._validate_content_validity(output, output_type)
        issues.extend(validity_issues)
        
        # Hallucination detection
        if self.config.enable_hallucination_detection:
            hallucination_issues = self._detect_hallucinations(output, context)
            issues.extend(hallucination_issues)
        
        # Security checks
        if self.config.enable_security_checks:
            security_issues = self._validate_security(output)
            issues.extend(security_issues)
        
        # Consistency checks
        consistency_issues = self._validate_consistency(output, context)
        issues.extend(consistency_issues)
        
        # Completeness checks
        completeness_issues = self._validate_completeness(output, output_type)
        issues.extend(completeness_issues)
        
        # Determine overall validity
        critical_issues = [issue for issue in issues if issue.severity == ValidationSeverity.CRITICAL]
        error_issues = [issue for issue in issues if issue.severity == ValidationSeverity.ERROR]
        
        is_valid = len(critical_issues) == 0 and len(error_issues) == 0
        
        return is_valid, issues
    
    def _validate_format(self, output: Any, output_type: str) -> List[ValidationIssue]:
        """Validate output format."""
        issues = []
        
        # Check if output is None or empty
        if output is None:
            issues.append(ValidationIssue(
                rule=ValidationRule.FORMAT_CHECK,
                severity=ValidationSeverity.ERROR,
                message="Output is None",
                confidence=1.0
            ))
            return issues
        
        # Check content length
        output_str = str(output)
        if len(output_str) > self.config.max_content_length:
            issues.append(ValidationIssue(
                rule=ValidationRule.FORMAT_CHECK,
                severity=ValidationSeverity.WARNING,
                message=f"Output exceeds maximum length ({len(output_str)} > {self.config.max_content_length})",
                actual=len(output_str),
                expected=self.config.max_content_length,
                confidence=0.8
            ))
        
        # Check for required fields based on output type
        if output_type in self.config.required_fields:
            required_fields = self.config.required_fields[output_type]
            
            if isinstance(output, dict):
                missing_fields = [field for field in required_fields if field not in output]
                if missing_fields:
                    issues.append(ValidationIssue(
                        rule=ValidationRule.FORMAT_CHECK,
                        severity=ValidationSeverity.ERROR,
                        message=f"Missing required fields: {missing_fields}",
                        field="required_fields",
                        expected=required_fields,
                        actual=list(output.keys()),
                        confidence=0.9
                    ))
            elif hasattr(output, '__dict__'):
                # Check object attributes
                missing_fields = [field for field in required_fields if not hasattr(output, field)]
                if missing_fields:
                    issues.append(ValidationIssue(
                        rule=ValidationRule.FORMAT_CHECK,
                        severity=ValidationSeverity.ERROR,
                        message=f"Missing required attributes: {missing_fields}",
                        field="required_attributes",
                        expected=required_fields,
                        actual=list(output.__dict__.keys()),
                        confidence=0.9
                    ))
        
        return issues
    
    def _validate_content_validity(self, output: Any, output_type: str) -> List[ValidationIssue]:
        """Validate content validity."""
        issues = []
        
        output_str = str(output)
        
        # Check for placeholder content
        placeholder_patterns = [
            r"TBD",
            r"TODO",
            r"FIXME",
            r"PLACEHOLDER",
            r"EXAMPLE",
            r"DUMMY",
            r"TEST",
            r"Lorem ipsum",
            r"Sample text",
            r"Mock data"
        ]
        
        for pattern in placeholder_patterns:
            if re.search(pattern, output_str, re.IGNORECASE):
                issues.append(ValidationIssue(
                    rule=ValidationRule.CONTENT_VALIDITY,
                    severity=ValidationSeverity.WARNING,
                    message=f"Contains placeholder content: {pattern}",
                    confidence=0.7
                ))
        
        # Check for repetitive content
        if self._is_repetitive(output_str):
            issues.append(ValidationIssue(
                rule=ValidationRule.CONTENT_VALIDITY,
                severity=ValidationSeverity.WARNING,
                message="Content appears to be repetitive",
                confidence=0.6
            ))
        
        # Check for unrealistic values
        if output_type == "validation_result":
            if hasattr(output, 'confidence_score'):
                if output.confidence_score > 0.99:
                    issues.append(ValidationIssue(
                        rule=ValidationRule.CONTENT_VALIDITY,
                        severity=ValidationSeverity.WARNING,
                        message="Unrealistically high confidence score",
                        field="confidence_score",
                        actual=output.confidence_score,
                        expected="< 0.99",
                        confidence=0.8
                    ))
        
        return issues
    
    def _detect_hallucinations(self, output: Any, context: Optional[Dict[str, Any]]) -> List[ValidationIssue]:
        """Detect potential hallucinations in output."""
        issues = []
        
        output_str = str(output)
        
        # Check for suspicious patterns that indicate hallucination
        suspicious_patterns = [
            r"I apologize, but I cannot",
            r"I don't have access to",
            r"I'm not able to",
            r"Unfortunately, I cannot",
            r"I'm sorry, but I",
            r"As an AI language model",
            r"I am an AI assistant",
            r"I don't have real-time",
            r"I cannot provide",
            r"I don't have the ability",
            r"I'm not programmed to",
            r"I don't have information about",
            r"I cannot access",
            r"I don't have data on",
            r"I'm not sure about",
            r"I don't know",
            r"I cannot tell you",
            r"I'm not certain",
            r"I cannot determine",
            r"I don't have details"
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, output_str, re.IGNORECASE):
                issues.append(ValidationIssue(
                    rule=ValidationRule.HALLUCINATION_DETECTION,
                    severity=ValidationSeverity.WARNING,
                    message=f"Potential hallucination detected: {pattern}",
                    confidence=0.7
                ))
        
        # Check for overly generic responses
        generic_phrases = [
            "This is a good question",
            "This is an interesting topic",
            "This depends on various factors",
            "There are many approaches",
            "It's important to consider",
            "This can vary",
            "This is subjective",
            "This requires more context"
        ]
        
        generic_count = sum(1 for phrase in generic_phrases if phrase.lower() in output_str.lower())
        if generic_count > 2:
            issues.append(ValidationIssue(
                rule=ValidationRule.HALLUCINATION_DETECTION,
                severity=ValidationSeverity.INFO,
                message="Output contains multiple generic phrases",
                confidence=0.5
            ))
        
        return issues
    
    def _validate_security(self, output: Any) -> List[ValidationIssue]:
        """Validate output for security issues."""
        issues = []
        
        output_str = str(output)
        
        # Check for dangerous patterns
        for pattern in self.config.suspicious_patterns:
            if re.search(pattern, output_str, re.IGNORECASE):
                issues.append(ValidationIssue(
                    rule=ValidationRule.SECURITY_CHECK,
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Potentially dangerous content detected: {pattern}",
                    confidence=0.9
                ))
        
        # Check for code injection attempts
        injection_patterns = [
            r"<script[^>]*>",
            r"javascript:",
            r"data:text/html",
            r"vbscript:",
            r"onload=",
            r"onerror=",
            r"onclick=",
            r"onmouseover=",
            r"onfocus=",
            r"onblur="
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, output_str, re.IGNORECASE):
                issues.append(ValidationIssue(
                    rule=ValidationRule.SECURITY_CHECK,
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Potential code injection detected: {pattern}",
                    confidence=0.9
                ))
        
        return issues
    
    def _validate_consistency(self, output: Any, context: Optional[Dict[str, Any]]) -> List[ValidationIssue]:
        """Validate output consistency."""
        issues = []
        
        # Check for internal contradictions
        output_str = str(output)
        
        # Check for contradictory statements
        contradictions = [
            ("yes", "no"),
            ("true", "false"),
            ("success", "failure"),
            ("valid", "invalid"),
            ("correct", "incorrect"),
            ("positive", "negative"),
            ("high", "low"),
            ("good", "bad"),
            ("recommended", "not recommended"),
            ("should", "should not")
        ]
        
        for word1, word2 in contradictions:
            if word1.lower() in output_str.lower() and word2.lower() in output_str.lower():
                issues.append(ValidationIssue(
                    rule=ValidationRule.CONSISTENCY_CHECK,
                    severity=ValidationSeverity.WARNING,
                    message=f"Potential contradiction detected: {word1} and {word2}",
                    confidence=0.6
                ))
        
        return issues
    
    def _validate_completeness(self, output: Any, output_type: str) -> List[ValidationIssue]:
        """Validate output completeness."""
        issues = []
        
        output_str = str(output)
        
        # Check for incomplete sentences
        incomplete_patterns = [
            r"[A-Z][^.!?]*$",  # Sentence ending without punctuation
            r"\.\.\.$",  # Trailing ellipsis
            r"etc\.$",  # Ending with etc.
            r"and so on$",
            r"and more$",
            r"and others$"
        ]
        
        for pattern in incomplete_patterns:
            if re.search(pattern, output_str, re.IGNORECASE):
                issues.append(ValidationIssue(
                    rule=ValidationRule.COMPLETENESS_CHECK,
                    severity=ValidationSeverity.INFO,
                    message="Output appears incomplete",
                    confidence=0.5
                ))
        
        # Check for minimum content length
        if len(output_str.strip()) < 10:
            issues.append(ValidationIssue(
                rule=ValidationRule.COMPLETENESS_CHECK,
                severity=ValidationSeverity.WARNING,
                message="Output is too short",
                actual=len(output_str),
                expected="> 10 characters",
                confidence=0.8
            ))
        
        return issues
    
    def _is_repetitive(self, text: str) -> bool:
        """Check if text is repetitive."""
        words = text.split()
        if len(words) < 10:
            return False
        
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # If any word appears more than 30% of the time, it's repetitive
        max_freq = max(word_freq.values())
        return max_freq > len(words) * 0.3
    
    def get_validation_summary(self, issues: List[ValidationIssue]) -> Dict[str, Any]:
        """Get a summary of validation issues."""
        severity_counts = {}
        rule_counts = {}
        
        for issue in issues:
            severity_counts[issue.severity.value] = severity_counts.get(issue.severity.value, 0) + 1
            rule_counts[issue.rule.value] = rule_counts.get(issue.rule.value, 0) + 1
        
        return {
            "total_issues": len(issues),
            "severity_breakdown": severity_counts,
            "rule_breakdown": rule_counts,
            "has_critical": ValidationSeverity.CRITICAL.value in severity_counts,
            "has_errors": ValidationSeverity.ERROR.value in severity_counts,
            "overall_confidence": 1.0 - (len(issues) * 0.1)  # Simple confidence calculation
        } 