-- Explicit DDL for the Postgres persistence adapter.
-- Column names are quoted to preserve exact camelCase identity
-- (planType, timeDepositId), matching the README's schema verbatim.

CREATE TABLE IF NOT EXISTS "timeDeposits" (
    id INTEGER PRIMARY KEY,
    "planType" VARCHAR NOT NULL,
    days INTEGER NOT NULL,
    balance NUMERIC NOT NULL
);

CREATE TABLE IF NOT EXISTS "withdrawals" (
    id INTEGER PRIMARY KEY,
    "timeDepositId" INTEGER NOT NULL REFERENCES "timeDeposits"(id),
    amount NUMERIC NOT NULL,
    date DATE NOT NULL
);
