"""Abstract repository PORT for time deposits.

Pure domain-facing boundary: imports only domain types (`TimeDeposit`,
`Withdrawal`). No framework, ORM, or DB driver import is allowed here --
concrete persistence (SQLAlchemy/psycopg) lives only in
`adapters/outbound/postgres/`.
"""

from abc import ABC, abstractmethod

from domain.withdrawal import Withdrawal
from time_deposit import TimeDeposit


class TimeDepositWithWithdrawals:
    """DTO pairing a deposit's fields with its withdrawals.

    Shaped for the GET /time-deposits response: id, planType, balance, days,
    withdrawals. Framework-free -- the HTTP adapter maps this to its own
    Pydantic schema, it is never serialized directly.
    """

    def __init__(self, id, planType, balance, days, withdrawals: list[Withdrawal]):
        self.id = id
        self.planType = planType
        self.balance = balance
        self.days = days
        self.withdrawals = withdrawals


class TimeDepositRepository(ABC):
    @abstractmethod
    def list_all(self) -> list[TimeDeposit]:
        """Return every persisted time deposit as a domain object."""
        ...

    @abstractmethod
    def list_with_withdrawals(self) -> list[TimeDepositWithWithdrawals]:
        """Return every deposit paired with its withdrawals (possibly empty)."""
        ...

    @abstractmethod
    def save_all(self, xs: list[TimeDeposit]) -> None:
        """Persist the (already recalculated) balances for the given deposits."""
        ...
