"""
PII redaction utilities for TractionBuild artifacts.
"""

import re
from typing import Any, Dict, List, Union

# Patterns for common PII
EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
PHONE_PATTERN = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
SSN_PATTERN = r'\b\d{3}[-]?\d{2}[-]?\d{4}\b'
IP_PATTERN = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'

def redact_pii(text: str) -> str:
    """Redact personally identifiable information from text."""
    if not isinstance(text, str):
        return str(text)

    # Replace with redaction markers
    text = re.sub(EMAIL_PATTERN, "[EMAIL_REDACTED]", text)
    text = re.sub(PHONE_PATTERN, "[PHONE_REDACTED]", text)
    text = re.sub(SSN_PATTERN, "[SSN_REDACTED]", text)
    text = re.sub(IP_PATTERN, "[IP_REDACTED]", text)

    return text

def redact_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively redact PII from dictionary values."""
    if not isinstance(data, dict):
        return data

    redacted = {}
    for key, value in data.items():
        if isinstance(value, dict):
            redacted[key] = redact_dict(value)
        elif isinstance(value, list):
            redacted[key] = [redact_dict(item) if isinstance(item, dict) else redact_pii(str(item)) for item in value]
        else:
            redacted[key] = redact_pii(str(value))

    return redacted
