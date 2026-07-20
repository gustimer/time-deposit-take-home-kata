# Brief Traceability — Time Deposit Refactoring Kata

Source of truth: [`README.md`](../README.md) (XA Bank Time Deposit brief). Re-read the brief verbatim before closing any row.

| ID | Brief text (verbatim) | Section | Expected evidence | Evidence (path/commit) | Status |
|----|-----------------------|---------|-------------------|------------------------|--------|
| R1a | "Create a RESTful API endpoint to update the balances of all time deposits in the database." | Requirements 1 | Update endpoint exists | `python/adapters/inbound/http/routers.py` | Closed |
| R1b | "**RESTful**" (graded adjective on the update endpoint) | Requirements 1 | Resource-oriented URI, no verb in path | `python/adapters/inbound/http/routers.py` (`POST /time-deposits/balance-updates`, justification comment on the route), `python/tests/unit/test_api_endpoints.py` | Closed |
| R2 | "Create a RESTful API endpoint to retrieve all time deposits." | Requirements 1 | GET collection endpoint | `python/adapters/inbound/http/routers.py` (`GET /time-deposits`) | Closed |
| R3 | "The GET endpoint should return … `id`, `planType`, `balance`, `days`, `withdrawals`" | Requirements 1 | Response schema fields | `python/adapters/inbound/http/schemas.py`, `python/tests/unit/test_api_endpoints.py` | Closed |
| R4 | "Store all time deposit plans in a database." | Requirements 2 | Persistent storage | `python/adapters/outbound/postgres/schema.sql`, `models.py` | Closed |
| R5 | "`timeDeposits`: id, planType, days, balance" | Requirements 2 | Table definition | `python/adapters/outbound/postgres/schema.sql` | Closed |
| R6 | "`withdrawals`: id, timeDepositId, amount, date" | Requirements 2 | Table definition | `python/adapters/outbound/postgres/schema.sql` | Closed |
| R7 | "Basic Plan: 1% interest" | Requirements 3 | Strategy + unit test | `python/domain/interest_strategies.py`, `tests/unit/test_interest_strategies.py` | Closed |
| R8 | "Student Plan: 3% interest (no interest after 1 year)" | Requirements 3 | Strategy + unit test | `python/domain/interest_strategies.py` | Closed |
| R9 | "Premium Plan: 5% interest (interest starts after 45 days)" | Requirements 3 | Strategy + unit test | `python/domain/interest_strategies.py` | Closed |
| R10 | "No interest is applied for the first 30 days for any existing plans." | Requirements 3 | Shared guard + tests | `python/domain/…` calculator guard, characterization tests | Closed |
| R11 | "Do not introduce breaking changes to the shared `TimeDeposit` class or modify the `updateBalance` method signature." | Requirements 4 | Public interface unchanged; characterization tests | `python/tests/unit/test_characterization.py` | Closed |
| R12 | "Ensure the design is extensible to accommodate future complexities in interest calculations." | Requirements 4 | Strategy registry: new plan = new class + entry | `python/domain/interest_strategies.py` (REGISTRY) | Closed |
| R13 | "Adhere to SOLID principles, design patterns, and clean code practices" | Requirements 5 | Strategy pattern, DI, layering | codebase-wide | Closed |
| R14 | "Set up an AI harness or agent workflow and use it throughout" | Requirements 6 | Harness used during development | `python/README.md` AI section | Closed |
| R15 | "Briefly document the tools and setup used" | Requirements 6 | Written documentation | `python/README.md` AI section | Closed |
| R16 | "Ensure your AI setup is practical and **reproducible**." | Requirements 6 | Config files in repo, not prose | `ai/README.md` (copy-and-run reproduction steps), `python/README.md` AI section | Closed |
| R17 | "Include any custom rules, system prompts, or agent configurations used." | Requirements 6 | Rules/agents committed | `ai/agents/` (18 agent definitions), `ai/skills/sdd-workflow/` (orchestrator workflow + phase conventions) | Closed |
| R18 | "Include a brief summary of which parts of the solution were AI-assisted and why." | Requirements 6 | Written summary | `python/README.md` AI section | Closed |
| G1 | "`TimeDepositCalculator.updateBalance` … behavior remains unchanged after refactoring." | Guidelines | Characterization tests green | `python/tests/unit/test_characterization.py` | Closed |
| G2 | "The final solution must include **exactly two API endpoints**." | Guidelines | Exactly 2 routes | `python/adapters/inbound/http/routers.py` | Closed |
| G3 | "Fork the repository … develop the solution there." | Guidelines | Fork, no upstream PR | repo origin | Closed |
| G4 | "Handling invalid input or exceptions is not required." | Guidelines | — | — | N/A (waived by brief) |
| G5 | "In case of ambiguity, make logical assumptions and justify them in code comments." | Guidelines | Justifying comments at decision points | module docstrings | Closed |
| P1 | "Use an OpenAPI Swagger contract." | Preferred Stack | Swagger UI reachable, documented | FastAPI `/docs`, `python/README.md` | Closed |
| P2 | "Embrace Hexagonal Architecture." | Preferred Stack | Structure *screams* hexagonal: domain entities inside `domain/`, no delivery concerns in ports | `python/domain/time_deposit.py` (canonical entity home; `time_deposit.py` reduced to a re-export shim), `python/ports/time_deposit_repository.py` (pure domain pairs), `python/application/read_models.py` (query read model) | Closed |
| P3 | "Follow atomic commit practices." | Preferred Stack | One concern per commit | `git log --oneline` | Closed |
| P4 | "Utilize testcontainers." | Preferred Stack | Integration tests via testcontainers | `python/tests/integration/test_postgres_repository.py` | Closed |
| P5 | "Leverage AI-assisted development tools for code generation, testing, and refactoring." | Preferred Stack | Documented AI-assisted workflow | `python/README.md` AI section | Closed |
| S1 | "Provide clear instructions on how to trigger the endpoints using the Swagger contract." | Submission | Run + Swagger instructions | `python/README.md` | Closed |

Status values:
- `Open` — no evidence yet.
- `In progress` — work started, evidence incomplete.
- `Closed` — evidence pointer filled in; verifiable by a cold reviewer in under a minute.
- `N/A` — only with a written justification in the row.

## Cold acceptance review

- Reviewer: fresh-context agent. Inputs: the original brief and the repository. Nothing else.
- Verdict per row: pass / fail with the concrete gap.
- Delivery is blocked until every row passes.

| ID | Verdict | Gap found |
|----|---------|-----------|
| — | pending | review runs after R1b, R16, R17, P2 close |
