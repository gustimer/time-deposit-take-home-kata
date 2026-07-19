"""List-deposits use case (application layer).

Depends only on the abstract `TimeDepositRepository` port. Returns the
framework-free `TimeDepositWithWithdrawals` DTOs from the port; the HTTP
adapter maps these to its own Pydantic response schemas -- no ORM/framework
type ever crosses this boundary.
"""

from ports.time_deposit_repository import TimeDepositRepository


class ListDepositsUseCase:
    def __init__(self, repository: TimeDepositRepository):
        self._repository = repository

    def execute(self):
        """Return every deposit paired with its withdrawals, for GET /time-deposits."""
        return self._repository.list_with_withdrawals()
