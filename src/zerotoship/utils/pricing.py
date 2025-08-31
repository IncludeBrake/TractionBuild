from dataclasses import dataclass
from typing import Dict, Tuple

"""Pricing utilities for LLM token usage.

This module provides a single source of truth for the cost of
individual language-model calls.  **Do not** scatter hard-coded
multipliers across the codebase—import from here instead.

All prices are expressed in *US dollars per 1 000 tokens* and MUST be
kept in sync with the vendor’s public pricing pages.  If you update a
price, bump the version field so historical rows remain auditable.
"""

@dataclass(frozen=True)
class Price:
    """Container for per-model pricing information."""

    # USD per 1 000 input tokens
    input_per_1k: float
    # USD per 1 000 output tokens
    output_per_1k: float
    # monotonically increasing schema version
    version: int = 1


# ---------------------------------------------------------------------------
# Central price table – add new models or revisions here only.
# ---------------------------------------------------------------------------
PRICES: Dict[str, Price] = {
    # OpenAI
    "gpt-4o-mini": Price(0.15, 0.60, 1),
    "gpt-4o": Price(5.00, 15.00, 1),
    # Anthropic
    "claude-3-sonnet": Price(3.00, 15.00, 1),
    # Fallback – will be used when model not explicitly listed
    # (kept intentionally low to prevent silent runaway cost)
}

# Default fallback cost.  Update conservatively – it applies to any
# unknown model names.
_FALLBACK_PRICE = Price(0.002, 0.002, 0)


def price_for(model: str) -> Price:
    """Return :class:`Price` entry for *model*, or a safe fallback."""

    return PRICES.get(model, _FALLBACK_PRICE)


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    """Compute dollar cost for a single call.

    Parameters
    ----------
    model
        Model name (must match the keys used in :data:`PRICES`).
    input_tokens / output_tokens
        Token counts reported by the LLM provider.
    """

    price = price_for(model)
    return (
        (input_tokens / 1000.0) * price.input_per_1k
        + (output_tokens / 1000.0) * price.output_per_1k
    )