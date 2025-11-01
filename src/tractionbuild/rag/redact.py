from __future__ import annotations
import re
import hashlib
from typing import Optional
from src.tractionbuild.policy.zones import Zone, mk_strategy

class Redactor:
    def __init__(self, strategy: str = "mask", salt: Optional[str] = None):
        self.strategy = strategy
        self.salt = salt or ""

    def redact(self, text: str) -> str:
        text = self._redact_emails(text)
        text = self._redact_phones(text)
        return text

    def _get_placeholder(self, pii_type: str, value: str) -> str:
        if self.strategy == "hash":
            hashed_value = hashlib.sha256((self.salt + value).encode()).hexdigest()[:8]
            return f"<{pii_type}:{hashed_value}>"
        return f"<{pii_type}>"

    def _redact_emails(self, text: str) -> str:
        return re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', lambda m: self._get_placeholder("email", m.group(0)), text)

    def _redact_phones(self, text: str) -> str:
        return re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', lambda m: self._get_placeholder("phone", m.group(0)), text)

class PolicyRedactor(Redactor):
    def __init__(self, zone: str = "amber", salt: str = ""):
        super().__init__(strategy="mask", salt=salt)
        self._policy = mk_strategy(Zone(zone.lower()), salt=salt)

    def redact(self, text: str) -> str:
        # Apply zone policy first, then base email/phone sweeps (idempotent)
        t = self._policy(text)
        return super().redact(t)