"""In-memory fake implementing TimeDepositRepository, for use-case tests.

Not a pytest module (no `test_*` symbols) -- shared test infra reused by
`test_update_balances_use_case.py` and `test_list_deposits_use_case.py`.
"""

from ports.time_deposit_repository import TimeDepositRepository


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
        # Pure domain pairs, mirroring the port contract:
        # (TimeDeposit, [Withdrawal, ...]). Assembling any read model from
        # these pairs is the use case's job, not the repository's.
        return [
            (
                td,
                [w for w in self._withdrawals if w.timeDepositId == td.id],
            )
            for td in self._deposits
        ]

    def save_all(self, xs):
        self.save_all_calls.append(list(xs))
        self._deposits = list(xs)
