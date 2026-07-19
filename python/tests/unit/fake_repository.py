"""In-memory fake implementing TimeDepositRepository, for use-case tests.

Not a pytest module (no `test_*` symbols) -- shared test infra reused by
`test_update_balances_use_case.py` and `test_list_deposits_use_case.py`.
"""

from ports.time_deposit_repository import (
    TimeDepositRepository,
    TimeDepositWithWithdrawals,
)


class FakeTimeDepositRepository(TimeDepositRepository):
    def __init__(self, deposits=None, withdrawals=None):
        self._deposits = list(deposits or [])
        # withdrawals: list of domain Withdrawal objects, matched to a
        # deposit via withdrawal.timeDepositId.
        self._withdrawals = list(withdrawals or [])
        self.save_all_calls: list[list] = []

    def list_all(self):
        return list(self._deposits)

    def list_with_withdrawals(self):
        result = []
        for td in self._deposits:
            td_withdrawals = [
                w for w in self._withdrawals if w.timeDepositId == td.id
            ]
            result.append(
                TimeDepositWithWithdrawals(
                    id=td.id,
                    planType=td.planType,
                    balance=td.balance,
                    days=td.days,
                    withdrawals=td_withdrawals,
                )
            )
        return result

    def save_all(self, xs):
        self.save_all_calls.append(list(xs))
        self._deposits = list(xs)
