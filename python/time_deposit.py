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

