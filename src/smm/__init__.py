"""
Synthetic Marketing Machine (SMM) for TractionBuild.
Generates market analysis, avatars, competitors, and marketing strategies.
"""

from .pipeline import SMM
from .guardrails import check_consistency

__all__ = ["SMM", "check_consistency"]
