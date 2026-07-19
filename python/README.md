# Time Deposit Service — Solution

Hexagonal FastAPI + PostgreSQL implementation of the XA Bank time-deposit
kata. This file documents how to run the solution and the AI-assisted
development workflow used to build it (README requirement 6). The original
kata instructions are unchanged in the repository root [`README.md`](../README.md).

## Architecture at a glance

```
python/
├── time_deposit.py              # preserved domain (TimeDeposit, TimeDepositCalculator) — untouched public API
├── domain/                      # interest strategy registry (basic/student/premium/null), zero framework imports
├── ports/                       # TimeDepositRepository ABC
├── application/                 # UpdateBalancesUseCase, ListDepositsUseCase
├── adapters/
│   ├── inbound/http/            # FastAPI app, routers, Pydantic schemas, DI providers
│   └── outbound/postgres/       # SQLAlchemy models, engine/session, repository, schema.sql, seed.sql
├── main.py                      # DI wiring + uvicorn entrypoint
├── docker-compose.yml           # db (postgres:16-alpine) + api services
├── Dockerfile                   # api service image
└── tests/                       # unit + testcontainers integration tests
```

## Running the service

### Option A — docker-compose (recommended)

From `python/`:

```bash
docker compose up -d --build
```

This starts:
- `db`: `postgres:16-alpine`, seeded automatically from
  `adapters/outbound/postgres/schema.sql` then `seed.sql` (mounted as
  `01-schema.sql` / `02-seed.sql` in `docker-entrypoint-initdb.d`, so the
  schema always applies before the seed data), with a `pg_isready`
  healthcheck.
- `api`: the FastAPI app, waiting on `db`'s healthcheck, exposed on
  `localhost:8000`.

Once healthy, open Swagger UI at **http://localhost:8000/docs**.

Tear down with `docker compose down -v` (the `-v` also drops the seeded
volume, so the next `up` reseeds from scratch).

### Option B — local uv environment

```bash
export PATH="$HOME/.local/bin:$PATH"   # if uv isn't already on PATH
cd python
uv sync
docker run --rm -d --name td-postgres \
  -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=time_deposit \
  -p 5432:5432 postgres:16-alpine
# apply schema + seed manually, e.g.:
docker exec -i td-postgres psql -U postgres -d time_deposit < adapters/outbound/postgres/schema.sql
docker exec -i td-postgres psql -U postgres -d time_deposit < adapters/outbound/postgres/seed.sql
uv run uvicorn main:app --reload
```

## Trying the endpoints via Swagger

1. Open **http://localhost:8000/docs**.
2. There are exactly two endpoints:
   - `POST /time-deposits/update-balances` — recalculates and persists
     interest for every stored deposit, returns the updated list.
   - `GET /time-deposits` — returns all deposits with nested `withdrawals`.
3. Sample flow: expand `POST /time-deposits/update-balances` → **Try it
   out** → **Execute** (no request body needed) to update all seeded
   balances, then expand `GET /time-deposits` → **Try it out** → **Execute**
   to see the persisted result, including a deposit with an empty
   `withdrawals: []` list.

Equivalent via `curl`:

```bash
curl -s -X POST http://localhost:8000/time-deposits/update-balances
curl -s http://localhost:8000/time-deposits
```

## Running the tests

```bash
export PATH="$HOME/.local/bin:$PATH"
cd python
uv run pytest -v
```

Unit tests run without Docker. The Postgres repository integration tests use
`testcontainers`, spinning up a real `postgres:16-alpine` container per test
session — Docker must be running for those to pass.

## AI-Assisted Development (README requirement 6)

### Tools and setup

- **Claude Code CLI** (Anthropic) as the primary coding agent, running an
  **SDD (spec-driven development) sub-agent workflow**: a phase-gated
  pipeline of `explore → propose → spec → design → tasks → apply → verify`,
  each phase run as a dedicated sub-agent with a narrow, explicit
  responsibility.
- **Engram**, a persistent-memory MCP server, stored every phase's artifact
  (proposal, spec, design, tasks, apply-progress) so each phase — and each
  apply batch, since implementation ran across several sessions — could
  reload full prior context instead of re-deriving it.
- **testcontainers** (Python) for real-Postgres integration tests, invoked
  by the agent as part of its verification loop, not only by a human.
- Standard supporting tooling: `uv` for dependency/venv management, `pytest`
  for the test runner, `docker`/`docker compose` for local runtime
  verification.

This setup is practical and reproducible: it only requires the Claude Code
CLI, the Engram MCP server, and this repository's checked-in
`pyproject.toml`/`uv.lock` — no bespoke infrastructure.

### Custom rules / agent configuration

- **Phase-gated SDD workflow**: a single orchestrator thread that never
  writes code itself — it delegates each phase (explore, spec, design,
  tasks, apply, verify) to a dedicated sub-agent, with the orchestrator
  reviewing the output between phases before proceeding.
- **Single-branch, atomic-commit delivery policy**: all work happens on one
  feature branch (`feat/time-deposit-solution`), with one focused
  conventional-commit per completed task (e.g. `refactor(python): extract
  interest strategy registry`), rather than one large commit — kept for
  reviewability even though this repo's contribution guidelines don't
  require a PR.
- **Strict TDD mode**: every behavior-changing task followed
  RED (write/confirm a failing test first) → GREEN (implement until it
  passes) → REFACTOR, enforced as a hard gate by the agent's own tasking
  rules, not just a suggestion.
- **Characterization tests before refactor**: before touching
  `TimeDepositCalculator.update_balance` at all, the agent first wrote
  characterization tests that pinned the *current* (pre-refactor) behavior
  by actually executing the unrefactored code and asserting on its real
  output (not hand-derived expected values). Only after that safety net was
  green did the strategy-pattern refactor happen, and the same
  characterization suite was re-run to prove the refactor produced
  bit-for-bit identical output.

### What was AI-assisted, and why

All of the implementation was AI-assisted, under human review at each SDD
phase gate (proposal, spec, design, tasks, and each apply batch were
reviewed before the agent proceeded to the next phase). Concretely:

- **Domain refactor** (`time_deposit.py` → `domain/interest_strategies.py`):
  AI-authored, guarded by characterization tests written first so the
  refactor was provably behavior-preserving.
- **Hexagonal boundaries** (`ports/`, `application/`,
  `adapters/inbound/http`, `adapters/outbound/postgres`): AI-authored
  following the design doc produced in the `sdd-design` phase, including
  the Decimal/float boundary conversion isolated to the repository adapter.
- **Tests** (unit, use-case, endpoint, and testcontainers integration):
  AI-authored RED-first per the strict-TDD gate.
- **Infra** (`docker-compose.yml`, `Dockerfile`, `seed.sql`) and this
  documentation: AI-authored in this final phase, then manually verified by
  actually bringing the stack up and exercising both endpoints end-to-end
  (see the apply-phase verification log for the exact commands and
  responses).

The `TimeDeposit` class and the original `test_time_deposit.py` file were
never modified — confirmed via `git diff` at the end of every phase — per
the kata's non-breaking-change constraint.
