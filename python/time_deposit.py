"""Backward-compatible import shim for the shared `TimeDeposit` class.

The brief forbids breaking changes to the shared `TimeDeposit` class, so the
historical import path `time_deposit` is preserved for external consumers
while the canonical home of the entity is `domain/`
(`domain/time_deposit.py`).
"""

from domain.time_deposit import TimeDeposit, TimeDepositCalculator

__all__ = ["TimeDeposit", "TimeDepositCalculator"]
