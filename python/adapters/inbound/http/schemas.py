"""Pydantic response schemas for the inbound HTTP adapter (FastAPI).

Framework-facing only -- these models shape the JSON response bodies AND
the auto-generated OpenAPI/Swagger schema for both endpoints. Domain and
application code never import these; the router maps domain/DTO objects
returned by the use cases to these `*Out` schemas explicitly.
"""

from datetime import date

from pydantic import BaseModel, ConfigDict


class WithdrawalOut(BaseModel):
    """Shape of a nested withdrawal entry: id, timeDepositId, amount, date."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    timeDepositId: int
    amount: float
    date: date


class TimeDepositOut(BaseModel):
    """Shape of a time deposit entry: id, planType, balance, days, withdrawals."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    planType: str
    balance: float
    days: int
    withdrawals: list[WithdrawalOut] = []
