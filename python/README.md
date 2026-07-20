# Time Deposit Service — Solution

Hexagonal FastAPI + PostgreSQL implementation of the XA Bank time-deposit
kata. This file documents how to run the solution and the AI-assisted
development workflow used to build it (README requirement 6). The original
kata instructions are unchanged in the repository root [`README.md`](../README.md).

## Architecture at a glance

```
python/
├── time_deposit.py              # import shim preserving the historical path — untouched public API
├── domain/                      # TimeDeposit + TimeDepositCalculator (canonical home) and the interest strategy registry, zero framework imports
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
   - `POST /time-deposits/balance-updates` — recalculates and persists
     interest for every stored deposit, returns the updated list.
   - `GET /time-deposits` — returns all deposits with nested `withdrawals`.
3. Sample flow: expand `POST /time-deposits/balance-updates` → **Try it
   out** → **Execute** (no request body needed) to update all seeded
   balances, then expand `GET /time-deposits` → **Try it out** → **Execute**
   to see the persisted result, including a deposit with an empty
   `withdrawals: []` list.

Equivalent via `curl`:

```bash
curl -s -X POST http://localhost:8000/time-deposits/balance-updates
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

The emphasis worth calling out: **the AI executed under human direction, with a
provable safety net around the one change the kata forbids breaking.** Before
`update_balance` was touched, 23 characterization tests pinned its exact output
by running the *original* code; the strategy refactor then had to keep every one
of them green and unchanged — making "no breaking changes" a proven fact, not a
promise. Every phase was human-reviewed before proceeding, and an independent
`sdd-verify` pass re-checked the result rather than trusting the implementer's
own report.

### Tools and setup

- **Claude Code CLI** (Anthropic), model **Claude Opus 4.8 (1M context)**, as
  the primary coding agent, running an **SDD (spec-driven development)
  sub-agent workflow**: a phase-gated pipeline of `explore → propose → spec →
  design → tasks → apply → verify`, each phase run as a dedicated sub-agent
  with a narrow, explicit responsibility.
- **[Gentle AI](https://github.com/Gentleman-Programming/gentle-ai)** — the
  agentic framework/harness layered on Claude Code that provides the SDD
  sub-agent pipeline, a bounded code-review lifecycle (`gentle-ai review`, 4R
  lenses), and CodeGraph code-intelligence. It is what turns the phase-gated
  workflow below from a convention into enforced tooling.
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
`pyproject.toml`/`uv.lock` — no bespoke infrastructure. The actual agent
definitions and workflow docs used are committed under [`ai/`](../ai/)
(see [`ai/README.md`](../ai/README.md) for copy-and-run reproduction steps).

### Custom rules / agent configuration

The concrete configuration files are committed in [`ai/`](../ai/): all 18
sub-agent definitions in [`ai/agents/`](../ai/agents/) and the SDD workflow
docs in [`ai/skills/sdd-workflow/`](../ai/skills/sdd-workflow/), with
reproduction instructions in [`ai/README.md`](../ai/README.md). In summary:

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
  documentation: AI-authored in this final phase, then verified end-to-end by
  bringing the stack up (`docker compose up -d --build`) and exercising both
  endpoints. `POST /time-deposits/balance-updates` and `GET /time-deposits`
  each returned HTTP 200, and the seeded `basic` deposit of `1234567.00` at
  `days=45` updated to `1235595.81` — the exact value pinned by the
  characterization tests — confirming identical behavior against real Postgres.

### Key decisions and rationale

- **Python + FastAPI**: Swagger/OpenAPI is auto-generated from the route
  signatures and Pydantic schemas — the lowest-friction way to satisfy the
  OpenAPI requirement within the deadline.
- **`float` in the domain, `Decimal` in the DB**: keeps the exact legacy
  arithmetic so `update_balance` stays behavior-identical, while `NUMERIC`
  columns provide banking-grade precision at rest. The conversion
  (`Decimal(str(x))` on write, `float(x)` on read) is isolated to the
  repository adapter, so precision concerns never leak into the domain or
  application layers.
- **Strategy pattern for interest**: honours the Open/Closed principle — a new
  plan type is a new strategy class plus one registry entry, with zero changes
  to `update_balance`.
- **Characterization tests before the refactor**: pinned the current behavior
  bit-for-bit by asserting the real output of the unrefactored code, proving
  the strategy refactor introduced zero drift.
- **`uv`**: a reproducible lockfile makes the environment installable for
  evaluators in a single command.
- **`docker-compose` with seed data**: one command brings up PostgreSQL + the
  API with sample data already loaded — the endpoints are demoable
  immediately.
- **Single branch, atomic commits**: a clean, reviewable history without the
  overhead of chained PRs.

The `TimeDeposit` class and the original `test_time_deposit.py` file were
never modified — confirmed via `git diff` at the end of every phase — per
the kata's non-breaking-change constraint. The class now lives verbatim in
`domain/time_deposit.py` (its canonical hexagonal home), while the
historical `time_deposit` import path is preserved through a thin re-export
shim, so external consumers — including the untouched
`test_time_deposit.py` — keep working unchanged.
