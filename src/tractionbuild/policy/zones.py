from __future__ import annotations
import re, hashlib
from enum import Enum
from typing import Callable

class Zone(str, Enum):
    GREEN  = "green"   # minimal redaction (safe/internal notes)
    AMBER  = "amber"   # standard redaction (most ops)
    RED    = "red"     # strict redaction (external/share)

def _hash(s: str, salt: str) -> str:
    return hashlib.sha256((salt + s).encode()).hexdigest()[:8]

def mk_strategy(zone: Zone, *, salt: str = "") -> Callable[[str], str]:
    """
    Returns a deterministic redaction function per zone.
    - GREEN: mask email/phone minimally
    - AMBER: mask + collapse IDs/tokens
    - RED: mask + hash placeholders + remove residual coordinates/addresses
    """
    EMAIL = r'[a-zA-Z0-9._%+-]+ @[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    PHONE = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
    ID    = r'\b(?:ssn|ein|tax|acct|iban|swift)[:\s]*[A-Za-z0-9\-]+\b'
    GEO   = r'\b(?:lat|lon|lng|latitude|longitude)[:\s]*-?\d+(\.\d+)?\b'

    def green(text: str) -> str:
        text = re.sub(EMAIL, "<email>", text)
        text = re.sub(PHONE, "<phone>", text)
        return text

    def amber(text: str) -> str:
        t = green(text)
        t = re.sub(ID, "<id>", t, flags=re.IGNORECASE)
        return t

    def red(text: str) -> str:
        t = re.sub(EMAIL, lambda m: f"<email:{_hash(m.group(0), salt)}>", text)
        t = re.sub(PHONE, lambda m: f"<phone:{_hash(m.group(0), salt)}>", t)
        t = re.sub(ID, "<id:hash>", t, flags=re.IGNORECASE)
        t = re.sub(GEO, "<geo>", t, flags=re.IGNORECASE)
        # collapse long digit/hex runs
        t = re.sub(r'\b[0-9A-Fa-f]{8,}\b', "<token>", t)
        return t

    return {Zone.GREEN: green, Zone.AMBER: amber, Zone.RED: red}[zone]
