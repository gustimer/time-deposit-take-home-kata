"""Dependency-injection providers for the inbound HTTP adapter.

Builds the real Postgres-backed repository and use cases per request via
FastAPI `Depends`. The DB engine is created lazily on first actual use
(`_session_factory`, memoized) rather than at module-import time, so
importing this module -- or building the app -- never forces a DB
connection. Tests override `get_repository` with an in-memory fake via
`app.dependency_overrides`, which also short-circuits `get_db_session` and
the engine entirely.
"""

from collections.abc import Generator
from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from adapters.outbound.postgres.db import make_engine, make_session_factory
from adapters.outbound.postgres.repository import SqlAlchemyTimeDepositRepository
from application.list_deposits import ListDepositsUseCase
from application.update_balances import UpdateBalancesUseCase
from ports.time_deposit_repository import TimeDepositRepository
from domain.time_deposit import TimeDepositCalculator


@lru_cache
def _session_factory():
    return make_session_factory(make_engine())


def get_db_session() -> Generator[Session, None, None]:
    session = _session_factory()()
    try:
        yield session
    finally:
        session.close()


def get_repository(
    session: Session = Depends(get_db_session),
) -> TimeDepositRepository:
    return SqlAlchemyTimeDepositRepository(session)


def get_update_balances_use_case(
    repository: TimeDepositRepository = Depends(get_repository),
) -> UpdateBalancesUseCase:
    return UpdateBalancesUseCase(repository, TimeDepositCalculator())


def get_list_deposits_use_case(
    repository: TimeDepositRepository = Depends(get_repository),
) -> ListDepositsUseCase:
    return ListDepositsUseCase(repository)
