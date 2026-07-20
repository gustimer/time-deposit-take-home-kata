"""Update-balances use case (application layer).

Depends only on the abstract `TimeDepositRepository` port and the existing
domain `TimeDepositCalculator` -- never on a concrete DB/framework adapter.
The interest-calculation logic itself is NOT reimplemented here; it is
delegated verbatim to `TimeDepositCalculator.update_balance`.
"""

from ports.time_deposit_repository import TimeDepositRepository
from domain.time_deposit import TimeDepositCalculator


class UpdateBalancesUseCase:
    def __init__(self, repository: TimeDepositRepository, calculator: TimeDepositCalculator):
        self._repository = repository
        self._calculator = calculator

    def execute(self):
        """Recalculate and persist balances for every deposit.

        Returns the full updated list so callers can present the outcome of
        the balance-update run without a second query.
        """
        deposits = self._repository.list_all()
        self._calculator.update_balance(deposits)
        self._repository.save_all(deposits)
        return deposits
