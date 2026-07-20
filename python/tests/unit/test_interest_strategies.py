"""Unit tests for the interest strategy registry (domain/interest_strategies.py).

These are new, focused unit tests for the strategy units themselves -- they
do not duplicate the `update_balance` characterization coverage in
`test_characterization.py`.
"""

from domain.interest_strategies import (
    REGISTRY,
    BasicInterestStrategy,
    NullStrategy,
    PremiumInterestStrategy,
    StudentInterestStrategy,
    get_strategy,
)
from domain.time_deposit import TimeDeposit


def make_td(plan_type, balance, days):
    return TimeDeposit(id=1, planType=plan_type, balance=balance, days=days)


class TestBasicInterestStrategy:
    def test_calculate_returns_raw_one_percent_monthly(self):
        td = make_td("basic", 1000.0, 31)
        assert BasicInterestStrategy().calculate(td) == (1000.0 * 0.01) / 12

    def test_calculate_has_no_day_subguard(self):
        # Basic has no additional day condition of its own; the caller
        # applies the shared `days > 30` guard, not the strategy.
        td = make_td("basic", 1000.0, 1)
        assert BasicInterestStrategy().calculate(td) == (1000.0 * 0.01) / 12


class TestStudentInterestStrategy:
    def test_calculate_below_366_days_returns_raw_three_percent_monthly(self):
        td = make_td("student", 1000.0, 365)
        assert StudentInterestStrategy().calculate(td) == (1000.0 * 0.03) / 12

    def test_calculate_at_366_days_returns_zero(self):
        td = make_td("student", 1000.0, 366)
        assert StudentInterestStrategy().calculate(td) == 0.0

    def test_calculate_above_366_days_returns_zero(self):
        td = make_td("student", 1000.0, 400)
        assert StudentInterestStrategy().calculate(td) == 0.0


class TestPremiumInterestStrategy:
    def test_calculate_above_45_days_returns_raw_five_percent_monthly(self):
        td = make_td("premium", 1000.0, 46)
        assert PremiumInterestStrategy().calculate(td) == (1000.0 * 0.05) / 12

    def test_calculate_at_45_days_returns_zero(self):
        td = make_td("premium", 1000.0, 45)
        assert PremiumInterestStrategy().calculate(td) == 0.0

    def test_calculate_below_45_days_returns_zero(self):
        td = make_td("premium", 1000.0, 10)
        assert PremiumInterestStrategy().calculate(td) == 0.0


class TestNullStrategy:
    def test_calculate_always_returns_zero(self):
        td = make_td("gold", 1000.0, 45)
        assert NullStrategy().calculate(td) == 0.0


class TestRegistry:
    def test_registry_maps_known_plan_types(self):
        assert isinstance(REGISTRY["basic"], BasicInterestStrategy)
        assert isinstance(REGISTRY["student"], StudentInterestStrategy)
        assert isinstance(REGISTRY["premium"], PremiumInterestStrategy)

    def test_get_strategy_returns_known_strategies(self):
        assert isinstance(get_strategy("basic"), BasicInterestStrategy)
        assert isinstance(get_strategy("student"), StudentInterestStrategy)
        assert isinstance(get_strategy("premium"), PremiumInterestStrategy)

    def test_get_strategy_unknown_plan_type_returns_null_strategy(self):
        strategy = get_strategy("gold")
        assert isinstance(strategy, NullStrategy)

    def test_get_strategy_unknown_plan_type_calculates_zero(self):
        strategy = get_strategy("unknown")
        td = make_td("unknown", 1000.0, 100)
        assert strategy.calculate(td) == 0.0
