"""SQLAlchemy repository ADAPTER implementing `TimeDepositRepository`.

The ONLY module allowed to import sqlalchemy/psycopg and convert between the
float-based domain and Decimal-based Postgres columns.

- Reads convert Decimal -> float (domain stays float-based, per design).
- Writes convert float -> Decimal via `Decimal(str(x))` -- NEVER
  `Decimal(x)` directly, which would carry binary-float drift into the
  stored value.
- `save_all` only updates `balance` (per the POST use case); id, planType,
  days, and withdrawals are left untouched.
"""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from adapters.outbound.postgres.models import TimeDepositModel
from domain.withdrawal import Withdrawal
from ports.time_deposit_repository import (
    TimeDepositRepository,
    TimeDepositWithWithdrawals,
)
from time_deposit import TimeDeposit


class SqlAlchemyTimeDepositRepository(TimeDepositRepository):
    def __init__(self, session: Session):
        self._session = session

    def list_all(self) -> list[TimeDeposit]:
        rows = self._session.execute(select(TimeDepositModel)).scalars().all()
        return [
            TimeDeposit(
                id=row.id,
                planType=row.plan_type,
                balance=float(row.balance),
                days=row.days,
            )
            for row in rows
        ]

    def list_with_withdrawals(self) -> list[TimeDepositWithWithdrawals]:
        stmt = select(TimeDepositModel).options(
            selectinload(TimeDepositModel.withdrawals)
        )
        rows = self._session.execute(stmt).scalars().all()
        return [
            TimeDepositWithWithdrawals(
                id=row.id,
                planType=row.plan_type,
                balance=float(row.balance),
                days=row.days,
                withdrawals=[
                    Withdrawal(
                        id=w.id,
                        timeDepositId=w.time_deposit_id,
                        amount=float(w.amount),
                        date=w.date,
                    )
                    for w in row.withdrawals
                ],
            )
            for row in rows
        ]

    def save_all(self, xs: list[TimeDeposit]) -> None:
        ids = [td.id for td in xs]
        rows_by_id = {
            row.id: row
            for row in self._session.execute(
                select(TimeDepositModel).where(TimeDepositModel.id.in_(ids))
            ).scalars()
        }
        for td in xs:
            rows_by_id[td.id].balance = Decimal(str(td.balance))
        self._session.commit()
