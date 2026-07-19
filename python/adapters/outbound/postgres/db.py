"""Engine/session factory for the Postgres adapter.

Connection parameters come from the `DATABASE_URL` environment variable
(a psycopg3 SQLAlchemy URL), with a sensible local-dev default. This module
-- along with models.py and repository.py -- is confined to
adapters/outbound/postgres/ and is the only place allowed to import
sqlalchemy/psycopg.
"""

import os

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

DEFAULT_DATABASE_URL = (
    "postgresql+psycopg://postgres:postgres@localhost:5432/time_deposit"
)


def get_database_url() -> str:
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


def make_engine(database_url: str | None = None, **kwargs) -> Engine:
    return create_engine(database_url or get_database_url(), **kwargs)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)
