"""Characterization tests for TimeDepositCalculator.update_balance.

These tests pin the EXACT current observable behavior of the legacy
`time_deposit.py` module BEFORE any refactor. They are a safety net, not
a specification of desired behavior: expected values below were obtained
by actually running the current implementation (see task notes), not by
hand-derivation.

Do NOT modify `time_deposit.py` to make these tests pass — if a refactor
changes any of these values, the refactor introduced a behavior change.
"""

import pytest

from domain.time_deposit import TimeDeposit, TimeDepositCalculator


def update_balance(plan_type, balance, days):
    """Helper: run update_balance on a single TimeDeposit, return resulting balance."""
    td = TimeDeposit(id=1, planType=plan_type, balance=balance, days=days)
    calc = TimeDepositCalculator()
    calc.update_balance([td])
    return td.balance


class TestBoundaryDays:
    """Pin the day-threshold boundaries exactly as implemented today."""

    def test_basic_days_30_no_interest(self):
        # td.days > 30 is required; 30 itself does not qualify.
        assert update_balance("basic", 1000.0, 30) == 1000.0

    def test_basic_days_31_interest_applies(self):
        assert update_balance("basic", 1000.0, 31) == 1000.83

    def test_premium_days_45_no_interest(self):
        # premium requires td.days > 45; 45 itself does not qualify.
        assert update_balance("premium", 1000.0, 45) == 1000.0

    def test_premium_days_46_interest_applies(self):
        assert update_balance("premium", 1000.0, 46) == 1004.17

    def test_student_days_365_interest_applies(self):
        # student requires td.days < 366; 365 qualifies.
        assert update_balance("student", 1000.0, 365) == 1002.5

    def test_student_days_366_no_interest(self):
        assert update_balance("student", 1000.0, 366) == 1000.0


class TestPlanTypesRepresentativeValues:
    """Each plan type at a representative days value, exact resulting balance."""

    def test_basic_plan(self):
        assert update_balance("basic", 1000.0, 31) == 1000.83

    def test_student_plan(self):
        assert update_balance("student", 1000.0, 365) == 1002.5

    def test_premium_plan(self):
        assert update_balance("premium", 1000.0, 46) == 1004.17


class TestKnownCharacterizationValue:
    """The known characterization value from the take-home brief.

    Verified by running the current (unrefactored) code directly:
    basic, balance=1234567.00, days=45 -> 1235595.81
    """

    def test_basic_large_balance_days_45(self):
        assert update_balance("basic", 1234567.00, 45) == 1235595.81


class TestUnknownPlanType:
    def test_unknown_plan_type_no_interest(self):
        # No branch matches 'gold' -> interest stays 0 even though days > 30.
        assert update_balance("gold", 1000.0, 31) == 1000.0

    def test_unknown_plan_type_no_interest_high_days(self):
        assert update_balance("gold", 1000.0, 45) == 1000.0


class TestMutationContract:
    def test_mutates_in_place_and_returns_none(self):
        td = TimeDeposit(id=1, planType="basic", balance=1000.0, days=31)
        calc = TimeDepositCalculator()

        result = calc.update_balance([td])

        assert result is None
        assert td.balance == 1000.83

    def test_multiple_deposits_all_updated(self):
        deposits = [
            TimeDeposit(id=1, planType="basic", balance=1000.0, days=31),
            TimeDeposit(id=2, planType="student", balance=1000.0, days=365),
            TimeDeposit(id=3, planType="premium", balance=1000.0, days=46),
            TimeDeposit(id=4, planType="gold", balance=1000.0, days=31),
        ]
        calc = TimeDepositCalculator()

        calc.update_balance(deposits)

        assert deposits[0].balance == 1000.83
        assert deposits[1].balance == 1002.5
        assert deposits[2].balance == 1004.17
        assert deposits[3].balance == 1000.0


@pytest.mark.parametrize(
    "plan_type,balance,days,expected",
    [
        ("basic", 1000.0, 30, 1000.0),
        ("basic", 1000.0, 31, 1000.83),
        ("basic", 1234567.00, 45, 1235595.81),
        ("student", 1000.0, 365, 1002.5),
        ("student", 1000.0, 366, 1000.0),
        ("premium", 1000.0, 45, 1000.0),
        ("premium", 1000.0, 46, 1004.17),
        ("gold", 1000.0, 31, 1000.0),
        ("gold", 1000.0, 45, 1000.0),
    ],
)
def test_update_balance_characterization(plan_type, balance, days, expected):
    assert update_balance(plan_type, balance, days) == expected
