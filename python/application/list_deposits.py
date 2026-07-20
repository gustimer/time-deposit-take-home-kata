"""List-deposits use case (application layer).

Depends only on the abstract `TimeDepositRepository` port. Assembles the
framework-free `TimeDepositWithWithdrawals` read model from the pure domain
pairs the port returns; inbound adapters map that read model to their own
presentation schemas -- no ORM/framework type ever crosses this boundary.
"""

from application.read_models import TimeDepositWithWithdrawals
from ports.time_deposit_repository import TimeDepositRepository


class ListDepositsUseCase:
    def __init__(self, repository: TimeDepositRepository):
        self._repository = repository

    def execute(self) -> list[TimeDepositWithWithdrawals]:
        """Return every deposit paired with its withdrawals as read models."""
        return [
            TimeDepositWithWithdrawals(
                id=deposit.id,
                planType=deposit.planType,
                balance=deposit.balance,
                days=deposit.days,
                withdrawals=withdrawals,
            )
            for deposit, withdrawals in self._repository.list_with_withdrawals()
        ]
