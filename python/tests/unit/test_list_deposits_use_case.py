"""Unit tests for ListDepositsUseCase (application layer).

Uses the in-memory FakeTimeDepositRepository -- no DB, no framework.
Verifies the use case assembles the `TimeDepositWithWithdrawals` read model
(id, planType, balance, days, withdrawals) from the pure domain pairs the
repository port returns.
"""

from application.list_deposits import ListDepositsUseCase
from application.read_models import TimeDepositWithWithdrawals
from domain.time_deposit import TimeDeposit
from domain.withdrawal import Withdrawal
from tests.unit.fake_repository import FakeTimeDepositRepository


class TestListDepositsUseCase:
    def test_deposit_with_withdrawals(self):
        deposit = TimeDeposit(id=1, planType="basic", balance=1000.83, days=31)
        w1 = Withdrawal(id=10, timeDepositId=1, amount=100.0, date="2026-01-01")
        w2 = Withdrawal(id=11, timeDepositId=1, amount=50.0, date="2026-02-01")
        repo = FakeTimeDepositRepository(deposits=[deposit], withdrawals=[w1, w2])
        use_case = ListDepositsUseCase(repo)

        result = use_case.execute()

        assert len(result) == 1
        entry = result[0]
        assert isinstance(entry, TimeDepositWithWithdrawals)
        assert entry.id == 1
        assert entry.planType == "basic"
        assert entry.balance == 1000.83
        assert entry.days == 31
        assert [w.id for w in entry.withdrawals] == [10, 11]
        assert entry.withdrawals[0].timeDepositId == 1
        assert entry.withdrawals[0].amount == 100.0
        assert entry.withdrawals[0].date == "2026-01-01"

    def test_deposit_with_no_withdrawals_has_empty_list(self):
        deposit = TimeDeposit(id=2, planType="student", balance=1002.5, days=365)
        repo = FakeTimeDepositRepository(deposits=[deposit], withdrawals=[])
        use_case = ListDepositsUseCase(repo)

        result = use_case.execute()

        assert len(result) == 1
        assert isinstance(result[0], TimeDepositWithWithdrawals)
        assert result[0].withdrawals == []

    def test_withdrawals_only_nested_under_owning_deposit(self):
        d1 = TimeDeposit(id=1, planType="basic", balance=1000.0, days=31)
        d2 = TimeDeposit(id=2, planType="basic", balance=2000.0, days=31)
        w = Withdrawal(id=10, timeDepositId=1, amount=100.0, date="2026-01-01")
        repo = FakeTimeDepositRepository(deposits=[d1, d2], withdrawals=[w])
        use_case = ListDepositsUseCase(repo)

        result = use_case.execute()

        by_id = {entry.id: entry for entry in result}
        assert len(by_id[1].withdrawals) == 1
        assert by_id[2].withdrawals == []
