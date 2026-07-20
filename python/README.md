# Time Deposit Service — Solution

Hexagonal FastAPI + PostgreSQL implementation of the XA Bank time-deposit
kata. This file documents how to run the solution and the checked-in
AI-workflow evidence for README requirement 6. The original
kata instructions are unchanged in the repository root [`README.md`](../README.md).

## Architecture at a glance

```
python/
├── time_deposit.py              # compatibility shim for the historical import path
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

Unit tests do not require Docker. The Postgres repository integration tests
use `testcontainers` with a real `postgres:16-alpine` container; Docker must
be running when those tests are included.

## AI-Assisted Development (README requirement 6)

The repository retains the AI-workflow artifacts and the delivery evidence
required by the brief. The following pointers are the source of truth; they
avoid treating undocumented execution history as proof.

| Topic | Repository evidence |
|-------|---------------------|
| Harness and configuration | [`ai/README.md`](../ai/README.md), [`ai/agents/`](../ai/agents/), and [`ai/skills/sdd-workflow/`](../ai/skills/sdd-workflow/) |
| Reproduction steps | [`ai/README.md`](../ai/README.md#reproducing-the-setup) documents the required copies and runtime assumptions |
| Delivery traceability | [`docs/brief-traceability.md`](../docs/brief-traceability.md), including the cold acceptance-review verdict |
| Supporting development tools | [`pyproject.toml`](./pyproject.toml) declares FastAPI, SQLAlchemy, `pytest`, `testcontainers`, and related dependencies; this README documents `uv` and Docker commands |

### Workflow and configuration

The primary coding agent was Claude Code CLI using Claude Opus 4.8.

The committed configuration defines an SDD workflow with the phases
`explore → propose → spec → design → tasks → apply → verify → archive`.
The `ai/agents/` directory contains 18 agent definitions, and
`ai/skills/sdd-workflow/` contains the shared workflow documents. Agent
frontmatter declares model aliases and tool access; the workflow documents
describe optional Engram memory and CodeGraph integration. See
[`ai/README.md`](../ai/README.md) for the concrete setup and reproduction
commands.

### Documented AI-assisted scope

The delivery documentation records AI assistance for the domain strategy
refactor, hexagonal adapters and use cases, tests, local Docker assets, and
documentation. The workflow separates planning, implementation, and
verification responsibilities so those areas can be reviewed against their
committed artifacts. The traceability table links requirement 6 to the
configuration and review evidence.

### Compatibility evidence

`tests/unit/test_characterization.py` specifies representative calculations,
day boundaries, unknown plan behavior, and in-place mutation for
`TimeDepositCalculator.update_balance`. `tests/unit/test_api_endpoints.py`
also asserts the two documented business routes and their response shape.
These are executable checks, not a claim in this document that they were run
at a particular time.

### Key decisions and rationale

- **Python + FastAPI**: Swagger/OpenAPI is generated from the route
  signatures and Pydantic schemas.
- **`float` in the domain, `Decimal` in the DB**: the domain retains its
  existing float arithmetic while `NUMERIC` columns persist balances. The conversion
  (`Decimal(str(x))` on write, `float(x)` on read) is isolated to the
  repository adapter, so precision concerns never leak into the domain or
  application layers.
- **Strategy pattern for interest**: honours the Open/Closed principle — a new
  plan type is a new strategy class plus one registry entry, with zero changes
  to `update_balance`.
- **Characterization tests**: capture representative legacy-compatible
  calculations and boundary conditions around `update_balance`.
- **`uv`**: `pyproject.toml` and the committed lockfile define the Python
  environment.
- **`docker compose` with seed data**: the compose file initializes PostgreSQL
  from the schema and seed SQL before starting the API service.
- **Atomic commits**: the history contains focused conventional commits for
  the implementation work.

The current repository preserves import compatibility for callers using
`from time_deposit import TimeDeposit, TimeDepositCalculator`:
`time_deposit.py` re-exports the classes from `domain/time_deposit.py`.
`test_time_deposit.py` continues to use that historical import path. This
documents the observable compatibility interface rather than making an
unverifiable claim about historical source identity.
