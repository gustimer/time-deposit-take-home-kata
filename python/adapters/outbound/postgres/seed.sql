-- Sample data for local/dev exploration via docker-compose.
-- Covers every plan type plus the interest-eligibility boundaries from the
-- domain spec (days<=30 grace period, student days>=366, premium days<=45),
-- and includes at least one deposit with zero withdrawals so GET
-- /time-deposits demonstrates an empty `withdrawals: []` list.
--
-- Runs after 01-schema.sql (lexical ordering in docker-entrypoint-initdb.d).
-- ON CONFLICT DO NOTHING keeps re-runs against an already-seeded volume safe.

INSERT INTO "timeDeposits" (id, "planType", days, balance) VALUES
    (1, 'basic',   45,  1234567.00), -- characterization value: -> 1235595.81 after update
    (2, 'student', 200, 5000.00),    -- student, days<366 -> interest applies
    (3, 'premium', 100, 10000.00),   -- premium, days>45 -> interest applies; NO withdrawals
    (4, 'premium', 45,  2000.00),    -- edge: days<=45 -> no premium interest yet
    (5, 'student', 400, 3000.00),    -- edge: days>=366 -> no student interest
    (6, 'basic',   15,  500.00)      -- edge: days<=30 grace period -> no interest at all
ON CONFLICT (id) DO NOTHING;

INSERT INTO "withdrawals" (id, "timeDepositId", amount, date) VALUES
    (1, 1, 100.00, '2026-01-15'),
    (2, 1, 250.50, '2026-03-01'),
    (3, 2, 500.00, '2026-02-10'),
    (4, 4, 75.25,  '2026-01-20'),
    (5, 5, 1000.00, '2026-04-05')
    -- deposits 3 and 6 intentionally have no withdrawals
ON CONFLICT (id) DO NOTHING;
