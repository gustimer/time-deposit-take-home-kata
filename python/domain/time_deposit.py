"""Time deposit entity and balance calculator (domain layer).

Canonical home of the shared `TimeDeposit` entity and the
`TimeDepositCalculator` domain service. Pure domain logic: no framework,
ORM, or delivery imports. The historical import path (`time_deposit` at the
package root) is preserved as a thin re-export shim for external consumers.
"""

from domain.interest_strategies import get_strategy


class TimeDeposit:
    def __init__(self, id, planType, balance, days):
        self.id = id
        self.planType = planType
        self.balance = balance
        self.days = days


class TimeDepositCalculator:

    def update_balance(self,xs):
        for td in xs:
            interest = 0
            if td.days > 30:
                # Per-plan rate/day-condition logic lives in the strategy
                # registry (domain/interest_strategies.py). Adding a new
                # plan type only requires a new strategy + registry entry --
                # never a change here. The shared `days > 30` guard and the
                # final rounding below remain cross-plan invariants.
                interest += get_strategy(td.planType).calculate(td)
            td.balance = round(td.balance + ((interest * 100) / 100), 2)
