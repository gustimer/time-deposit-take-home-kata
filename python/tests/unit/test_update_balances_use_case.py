"""Unit tests for UpdateBalancesUseCase (application layer).

Uses the in-memory FakeTimeDepositRepository -- no DB, no framework. Exercises
the same domain interest logic already pinned by
`test_characterization.py`, so the expected balances below reuse those
known values (e.g. basic/1234567.00/days=45 -> 1235595.81).
"""

from application.update_balances import UpdateBalancesUseCase
from tests.unit.fake_repository import FakeTimeDepositRepository
from domain.time_deposit import TimeDeposit, TimeDepositCalculator


def make_repo(*deposits):
    return FakeTimeDepositRepository(deposits=list(deposits))


class TestUpdateBalancesUseCase:
    def test_recalculates_and_persists_balances(self):
        deposit = TimeDeposit(id=1, planType="basic", balance=1234567.00, days=45)
        repo = make_repo(deposit)
        use_case = UpdateBalancesUseCase(repo, TimeDepositCalculator())

        result = use_case.execute()

        assert deposit.balance == 1235595.81
        assert result[0].balance == 1235595.81

    def test_persists_via_save_all(self):
        deposit = TimeDeposit(id=1, planType="basic", balance=1000.0, days=31)
        repo = make_repo(deposit)
        use_case = UpdateBalancesUseCase(repo, TimeDepositCalculator())

        use_case.execute()

        assert len(repo.save_all_calls) == 1
        assert repo.save_all_calls[0][0].balance == 1000.83

    def test_returns_full_updated_list(self):
        d1 = TimeDeposit(id=1, planType="basic", balance=1000.0, days=31)
        d2 = TimeDeposit(id=2, planType="student", balance=1000.0, days=365)
        d3 = TimeDeposit(id=3, planType="gold", balance=1000.0, days=31)
        repo = make_repo(d1, d2, d3)
        use_case = UpdateBalancesUseCase(repo, TimeDepositCalculator())

        result = use_case.execute()

        assert [td.id for td in result] == [1, 2, 3]
        assert [td.balance for td in result] == [1000.83, 1002.5, 1000.0]

    def test_no_deposits_returns_empty_list_and_still_saves(self):
        repo = make_repo()
        use_case = UpdateBalancesUseCase(repo, TimeDepositCalculator())

        result = use_case.execute()

        assert result == []
        assert repo.save_all_calls == [[]]
