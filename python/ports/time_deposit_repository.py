"""Abstract repository PORT for time deposits.

Pure domain-facing boundary: imports only domain types (`TimeDeposit`,
`Withdrawal`). No framework, ORM, or DB driver import is allowed here --
concrete persistence (SQLAlchemy/psycopg) lives only in
`adapters/outbound/postgres/`.
"""

from abc import ABC, abstractmethod

from domain.time_deposit import TimeDeposit
from domain.withdrawal import Withdrawal


class TimeDepositRepository(ABC):
    @abstractmethod
    def list_all(self) -> list[TimeDeposit]:
        """Return every persisted time deposit as a domain object."""
        ...

    @abstractmethod
    def list_with_withdrawals(self) -> list[tuple[TimeDeposit, list[Withdrawal]]]:
        """Return every deposit paired with its withdrawals (possibly empty).

        Pure domain data only: each element is a `(TimeDeposit,
        [Withdrawal, ...])` pair. Any caller-facing read model is assembled
        in the application layer, never here.
        """
        ...

    @abstractmethod
    def save_all(self, xs: list[TimeDeposit]) -> None:
        """Persist the (already recalculated) balances for the given deposits."""
        ...
