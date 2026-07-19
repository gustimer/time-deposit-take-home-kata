"""SQLAlchemy 2.0 declarative ORM models for the Postgres adapter.

Maps the exact camelCase DB columns (planType, timeDepositId) from
schema.sql to clear Python attribute names via `mapped_column(...)`, so the
DDL stays byte-identical to the README while Python code stays idiomatic.

ORM/DB imports are confined to this package (adapters/outbound/postgres/) --
domain, ports, and application code never import sqlalchemy or psycopg.
"""

from __future__ import annotations

import datetime
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TimeDepositModel(Base):
    __tablename__ = "timeDeposits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_type: Mapped[str] = mapped_column("planType", String, nullable=False)
    days: Mapped[int] = mapped_column(Integer, nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric, nullable=False)

    withdrawals: Mapped[list["WithdrawalModel"]] = relationship(
        back_populates="time_deposit"
    )


class WithdrawalModel(Base):
    __tablename__ = "withdrawals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    time_deposit_id: Mapped[int] = mapped_column(
        "timeDepositId", Integer, ForeignKey("timeDeposits.id"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)

    time_deposit: Mapped["TimeDepositModel"] = relationship(
        back_populates="withdrawals"
    )
