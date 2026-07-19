"""Per-plan interest calculation strategies.

Extends the legacy `TimeDepositCalculator.update_balance` if/elif ladder into
a Strategy pattern: each plan type gets its own `InterestStrategy`, looked up
via `REGISTRY`. `update_balance` keeps the `days > 30` guard, the `+=`
accumulation, and the final `round(...)` call unchanged; it only delegates
the per-plan branch to `REGISTRY.get(plan_type, NullStrategy())`.

Extensibility: adding a new plan type requires ONLY a new `InterestStrategy`
subclass plus one `REGISTRY` entry below -- `update_balance` never needs to
change.

This module has zero framework/DB imports: it is pure domain logic.

The arithmetic expressions below are copied verbatim from the legacy
implementation (e.g. `(balance * 0.03) / 12`) rather than algebraically
simplified, to avoid any float rounding drift relative to the
characterization tests.
"""

from typing import Protocol


class InterestStrategy(Protocol):
    """Computes the RAW, unrounded monthly interest for a time deposit.

    Implementations do not apply the `days > 30` guard (that stays in
    `update_balance`, as a cross-plan invariant) but MAY apply their own
    plan-specific day sub-guards, mirroring the legacy nested conditions.
    """

    def calculate(self, td) -> float:
        ...


class BasicInterestStrategy:
    """Basic plan: 1% annual rate, no additional day sub-guard.

    Legacy: `interest += (td.balance * 0.01) / 12` (only reached when
    `td.days > 30`, guarded by the caller).
    """

    def calculate(self, td) -> float:
        return (td.balance * 0.01) / 12


class StudentInterestStrategy:
    """Student plan: 3% annual rate, only while `td.days < 366`.

    Legacy: `if td.days < 366: interest += (td.balance * 0.03)/12`.
    """

    def calculate(self, td) -> float:
        if td.days < 366:
            return (td.balance * 0.03) / 12
        return 0.0


class PremiumInterestStrategy:
    """Premium plan: 5% annual rate, only while `td.days > 45`.

    Legacy: `if td.days > 45: interest += (td.balance * 0.05)/12`.
    """

    def calculate(self, td) -> float:
        if td.days > 45:
            return (td.balance * 0.05) / 12
        return 0.0


class NullStrategy:
    """Fallback for unknown plan types.

    Mirrors the legacy behavior of silently contributing zero interest when
    no `if`/`elif` branch matches (there was no trailing `else`).
    """

    def calculate(self, td) -> float:
        return 0.0


REGISTRY: dict[str, InterestStrategy] = {
    "basic": BasicInterestStrategy(),
    "student": StudentInterestStrategy(),
    "premium": PremiumInterestStrategy(),
}


def get_strategy(plan_type: str) -> InterestStrategy:
    """Look up the strategy for `plan_type`, defaulting to `NullStrategy`."""
    return REGISTRY.get(plan_type, NullStrategy())
