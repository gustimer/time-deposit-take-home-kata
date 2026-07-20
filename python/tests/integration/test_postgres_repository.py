"""Testcontainers-backed integration tests for the Postgres repository
adapter -- the boundary that owns Decimal<->float conversion (the design's
flagged precision risk).

Requires Docker. Marked `@pytest.mark.integration` (registered in
pyproject.toml) but runs by default in this project's test suite.

A single Postgres container is started once per module and reused across
all tests here for speed; each test truncates the tables first so tests
stay isolated from each other.
"""

import datetime
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

from adapters.outbound.postgres.repository import SqlAlchemyTimeDepositRepository
from domain.time_deposit import TimeDeposit

SCHEMA_SQL = (
    Path(__file__).resolve().parents[2]
    / "adapters"
    / "outbound"
    / "postgres"
    / "schema.sql"
).read_text()


@pytest.fixture(scope="module")
def postgres_container():
    with PostgresContainer("postgres:16-alpine", driver="psycopg") as container:
        yield container


@pytest.fixture(scope="module")
def db_engine(postgres_container):
    engine = create_engine(postgres_container.get_connection_url())
    with engine.begin() as conn:
        conn.execute(text(SCHEMA_SQL))
    yield engine
    engine.dispose()


@pytest.fixture()
def db_session(db_engine):
    session_factory = sessionmaker(bind=db_engine, expire_on_commit=False)
    session = session_factory()
    # Isolate each test: clear both tables (children before parent, FK order).
    session.execute(text('TRUNCATE TABLE "withdrawals", "timeDeposits" RESTART IDENTITY CASCADE'))
    session.commit()
    yield session
    session.close()


@pytest.fixture()
def repository(db_session):
    return SqlAlchemyTimeDepositRepository(db_session)


@pytest.mark.integration
def test_schema_uses_exact_camelcase_columns(db_engine):
    with db_engine.connect() as conn:
        deposit_cols = set(
            conn.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'timeDeposits'"
                )
            )
            .scalars()
            .all()
        )
        withdrawal_cols = set(
            conn.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'withdrawals'"
                )
            )
            .scalars()
            .all()
        )

    assert deposit_cols == {"id", "planType", "days", "balance"}
    assert withdrawal_cols == {"id", "timeDepositId", "amount", "date"}


@pytest.mark.integration
def test_list_all_returns_domain_time_deposits_with_float_balance(
    db_session, repository
):
    db_session.execute(
        text(
            'INSERT INTO "timeDeposits" (id, "planType", days, balance) '
            "VALUES (1, 'basic', 45, 1234567.00)"
        )
    )
    db_session.commit()

    result = repository.list_all()

    assert len(result) == 1
    deposit = result[0]
    assert isinstance(deposit, TimeDeposit)
    assert deposit.id == 1
    assert deposit.planType == "basic"
    assert deposit.days == 45
    assert deposit.balance == 1234567.00
    assert isinstance(deposit.balance, float)


@pytest.mark.integration
def test_list_with_withdrawals_nests_correctly_including_empty(
    db_session, repository
):
    db_session.execute(
        text(
            'INSERT INTO "timeDeposits" (id, "planType", days, balance) VALUES '
            "(1, 'basic', 45, 1000.00), (2, 'student', 100, 500.00)"
        )
    )
    db_session.execute(
        text(
            'INSERT INTO "withdrawals" (id, "timeDepositId", amount, date) VALUES '
            "(1, 1, 100.50, '2026-01-15'), (2, 1, 50.25, '2026-02-01')"
        )
    )
    db_session.commit()

    result = repository.list_with_withdrawals()
    by_id = {deposit.id: (deposit, withdrawals) for deposit, withdrawals in result}

    deposit_1, withdrawals_1 = by_id[1]
    assert isinstance(deposit_1, TimeDeposit)
    assert len(withdrawals_1) == 2
    withdrawals_by_id = {w.id: w for w in withdrawals_1}
    assert withdrawals_by_id[1].timeDepositId == 1
    assert withdrawals_by_id[1].amount == 100.50
    assert isinstance(withdrawals_by_id[1].amount, float)
    assert withdrawals_by_id[1].date == datetime.date(2026, 1, 15)
    assert withdrawals_by_id[2].amount == 50.25
    assert withdrawals_by_id[2].date == datetime.date(2026, 2, 1)

    _, withdrawals_2 = by_id[2]
    assert withdrawals_2 == []


@pytest.mark.integration
def test_save_all_round_trips_without_precision_loss(db_session, repository):
    db_session.execute(
        text(
            'INSERT INTO "timeDeposits" (id, "planType", days, balance) '
            "VALUES (1, 'basic', 45, 1000.00)"
        )
    )
    db_session.commit()

    updated = TimeDeposit(id=1, planType="basic", balance=1235595.81, days=45)
    repository.save_all([updated])

    reread = repository.list_all()
    assert reread[0].balance == 1235595.81
    assert isinstance(reread[0].balance, float)

    raw_balance = db_session.execute(
        text('SELECT balance FROM "timeDeposits" WHERE id = 1')
    ).scalar_one()
    assert raw_balance == Decimal("1235595.81")


@pytest.mark.integration
def test_save_all_only_updates_balance_leaves_other_fields_unchanged(
    db_session, repository
):
    db_session.execute(
        text(
            'INSERT INTO "timeDeposits" (id, "planType", days, balance) '
            "VALUES (1, 'premium', 46, 1000.00)"
        )
    )
    db_session.commit()

    updated = TimeDeposit(id=1, planType="premium", balance=1004.17, days=46)
    repository.save_all([updated])

    reread = repository.list_all()[0]
    assert reread.planType == "premium"
    assert reread.days == 46
    assert reread.balance == 1004.17
