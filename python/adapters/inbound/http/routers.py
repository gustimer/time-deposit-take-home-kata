"""FastAPI routes for the time-deposit HTTP adapter.

Exactly two business endpoints, per spec:
- POST /time-deposits/update-balances
- GET  /time-deposits

Use case instances are obtained via `Depends(...)` provider functions
(`adapters/inbound/http/deps.py`) so tests can override the repository they
are built from via `app.dependency_overrides`. Domain/DTO objects returned
by the use cases are mapped explicitly to `*Out` schemas here -- the same
explicit-mapping convention already used by the Postgres adapter -- rather
than relying on Pydantic's `from_attributes` to invent a default
`withdrawals` list for `TimeDeposit` (which has no `withdrawals`
attribute at all, unlike the `TimeDepositWithWithdrawals` DTO).
"""

from fastapi import APIRouter, Depends

from adapters.inbound.http.deps import (
    get_list_deposits_use_case,
    get_update_balances_use_case,
)
from adapters.inbound.http.schemas import TimeDepositOut, WithdrawalOut
from application.list_deposits import ListDepositsUseCase
from application.update_balances import UpdateBalancesUseCase

router = APIRouter(tags=["time-deposits"])


def _to_withdrawal_out(withdrawal) -> WithdrawalOut:
    return WithdrawalOut(
        id=withdrawal.id,
        timeDepositId=withdrawal.timeDepositId,
        amount=withdrawal.amount,
        date=withdrawal.date,
    )


def _to_time_deposit_out(deposit) -> TimeDepositOut:
    withdrawals = getattr(deposit, "withdrawals", [])
    return TimeDepositOut(
        id=deposit.id,
        planType=deposit.planType,
        balance=deposit.balance,
        days=deposit.days,
        withdrawals=[_to_withdrawal_out(w) for w in withdrawals],
    )


@router.post("/time-deposits/update-balances", response_model=list[TimeDepositOut])
def update_balances(
    use_case: UpdateBalancesUseCase = Depends(get_update_balances_use_case),
):
    """Recalculate and persist balances for every deposit; return the updated list."""
    return [_to_time_deposit_out(td) for td in use_case.execute()]


@router.get("/time-deposits", response_model=list[TimeDepositOut])
def list_deposits(
    use_case: ListDepositsUseCase = Depends(get_list_deposits_use_case),
):
    """Return every deposit with id, planType, balance, days, withdrawals."""
    return [_to_time_deposit_out(td) for td in use_case.execute()]
