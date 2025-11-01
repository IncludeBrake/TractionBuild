from __future__ import annotations
from dataclasses import dataclass

@dataclass
class TokenBudget:
    hard_cap: int
    soft_cap: int | None = None

    calls: int = 0
    in_tokens: int = 0
    out_tokens: int = 0

    def can_spend(self, will_spend: int) -> bool:
        return (self.in_tokens + self.out_tokens + will_spend) <= self.hard_cap

    def over_soft(self) -> bool:
        return self.soft_cap is not None and (self.in_tokens + self.out_tokens) >= self.soft_cap
