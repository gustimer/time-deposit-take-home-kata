"""Withdrawal domain type.

Framework/DB-free, mirrors the `withdrawals` table shape from the spec:
`id`, `timeDepositId` (FK), `amount`, `date`.
"""


class Withdrawal:
    def __init__(self, id, timeDepositId, amount, date):
        self.id = id
        self.timeDepositId = timeDepositId
        self.amount = amount
        self.date = date
