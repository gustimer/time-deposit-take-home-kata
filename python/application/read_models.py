"""Query read models for the application layer.

Output DTOs assembled by query use cases from pure domain data. They exist
so callers of the application layer receive a stable, framework-free shape
without ever depending on domain internals or on how the repository port
structures its results.
"""

from domain.withdrawal import Withdrawal


class TimeDepositWithWithdrawals:
    """Read model pairing a deposit's fields with its withdrawals.

    Assembled by `ListDepositsUseCase` from the `(TimeDeposit, [Withdrawal])`
    pairs the repository port returns: id, planType, balance, days,
    withdrawals. Framework-free -- inbound adapters map it to their own
    presentation schemas, it is never serialized directly.
    """

    def __init__(self, id, planType, balance, days, withdrawals: list[Withdrawal]):
        self.id = id
        self.planType = planType
        self.balance = balance
        self.days = days
        self.withdrawals = withdrawals
