# PERT Estimation App — Constitution

## Preamble

This constitution is the **single source of truth** for every decision in the PERT Estimation
App project. It was written after a full post-mortem of v1 and is designed to make past
mistakes structurally impossible — including when the implementer is an AI agent.

**Supremacy rule:** when this document conflicts with any other source — code comments, agent
instructions, external examples — this constitution prevails. No exceptions.

---

## Principle I. Schema-First Pipeline (Single Source of Truth)

The backend (FastAPI / Python) is the **sole authoritative source** for all business logic
and PERT calculations. The frontend is a pure UI shell with zero business logic of its own.

### Mandatory development pipeline

```
1. Hand-write and review Pydantic models (architect sign-off required)
2. FastAPI auto-generates openapi.json from those models
3. `just fe-generate` runs openapi-typescript against the live backend → frontend/src/types/api.ts
4. Next.js consumes ONLY generated types — manual TypeScript interfaces for API data: PROHIBITED
```

**PROHIBITED:**
- Writing TypeScript interfaces for API data by hand
- Changing the DB schema or Pydantic models before updating the specification first
- Implementing PERT formulas on the frontend as an authoritative source
  (JS mirror is optimistic preview only)

**REQUIRED:**
- Every `PATCH /items/{id}` response MUST include all calculated fields:
  `t_expected`, `spread`, `sigma`, `variance`, `hidden_reserve`, `total_effort`, `duration_days`
- Frontend MUST re-sync from the backend response on every save (debounce ≤ 2 s)

**Rationale:** Formula drift between JS and Python is rated High Business Impact /
High Technical Risk (AR-01). Backend authority eliminates drift structurally. (ATAM AD-02)

---

## Principle II. Vertical Slice Architecture + Zero-Ops MVP

### Code structure

Code is organised by **functional feature**, not by technical layer:

```
backend/
  src/
    features/
      auth/           # routes, commands, models, services for authentication
      sessions/       # routes, commands, models for estimation sessions
      items/          # routes, commands, models for PERT items
      export/         # routes, commands, port, tracker adapters
      settings/       # routes, commands, TrackerConnection management
    core/
      config.py       # SOLE configuration entry point — pydantic-settings
      db.py
      security.py
      logging.py
    shared/
      models/         # ErrorResponse, PartialResultResponse, base schemas
      protocols/      # cross-feature Protocol interfaces

frontend/
  src/
    features/
      {feature}/
        components/   # presentational only — zero logic
        hooks/        # client-side state (islands only)
        actions/      # Next.js Server Actions
    components/       # global presentational components
    types/            # ONLY openapi-typescript generated output (do not edit manually)
```

**File size limit: 200 lines.** Exceeding the limit requires decomposition before
writing the next line of code — no exceptions, no deferral.

### MVP constraints (immutable until explicit trigger)

- SQLite with WAL mode is the only database for MVP
- Single-tenant, single-server, ≤ 5 concurrent users
- Multi-tenancy (`org_id`) MUST NOT appear in the MVP schema
- Soft cap: 100 items per session

**Stack re-evaluation triggers:**

| ID | Trigger | Action |
|----|---------|--------|
| SP-01 | > 3 concurrent editors OR p95 SQLite lock wait > 100 ms | Migrate to PostgreSQL + asyncpg |
| SP-02 | Auto-save UX complaints | Re-tune debounce interval |
| SP-03 | Sessions routinely exceed 100 items | Add virtual list + batch PATCH |
| SP-04 | Token input friction | Implement OAuth 2.0 flow |

---

## Principle III. Test-First & Formula Parity (NON-NEGOTIABLE)

TDD is mandatory for all PERT calculation logic. Tests MUST be written and pass the
Red-Green-Refactor cycle before implementation proceeds.

- PERT unit tests: **100% line coverage**, including edge cases (O = M = P, zero values,
  maximum spread)
- Property-based tests (Hypothesis): ≥ 1 000 random valid inputs; Python backend and
  JavaScript preview MUST produce identical results; shared test vectors stored as a JSON
  fixture consumed by both suites (ATAM AR-01)
- Export service: ≥ 85% coverage via mock adapters
- E2E critical path: login → session creation → O/M/P entry → Approve → Export preview

**Merging without all CI tests passing is PROHIBITED.**

---

## Principle IV. Port Abstraction for Every External Dependency

`IssueTrackerPort` is the mandatory Protocol for all issue trackers. This is a specific
instance of the general rule: **every external dependency (tracker, email, storage, any
third-party API) MUST have a defining Protocol**.

```python
class IssueTrackerPort(Protocol):
    async def test_connection(self) -> ConnectionResult: ...
    async def list_projects(self) -> list[Project]: ...
    async def get_project_fields(self, project_id: str) -> list[Field]: ...
    async def create_issue(self, project_id: str, payload: IssuePayload) -> CreatedIssue: ...
```

**PROHIBITED:**
- Importing `YouTrackAdapter` (or any concrete adapter) directly inside a service
- Creating inter-service dependencies via direct class imports (Protocol only)
- Business logic depending on the FastAPI framework (routers delegate only)

**Tracker switch cost target:** < 2 person-days. Adding a new tracker = one new adapter
class + DI registration. Changes to `ExportService` for a tracker addition: PROHIBITED.

---

## Principle V. Data Contracts & Error Handling

### The project is built around explicit, typed contracts. `Any` in Python or `any` in TypeScript is treated as a compilation error.

### Unified error model

```python
class ErrorResponse(BaseModel):
    code: str            # machine-readable: "VALIDATION_ERROR", "NOT_FOUND", etc.
    message: str         # human-readable message shown to the user
    detail: str | None   # optional technical context (DEBUG mode only)
    request_id: str      # for log correlation
```

All `HTTPException` instances MUST be wrapped via `ErrorResponse`.
Direct `raise HTTPException(detail="some string")` in business logic: **PROHIBITED**.

### Partial result model (export and batch operations)

```python
class PartialResultResponse(BaseModel):
    succeeded: list[ItemResult]
    failed: list[FailedItemResult]  # includes item_id + ErrorResponse per failure
    total: int
```

HTTP `207 Multi-Status` for operations with partial results.

### Typing rules

- `NewType` for every ID type:
  `SessionId = NewType("SessionId", uuid.UUID)`,
  `ItemId = NewType("ItemId", uuid.UUID)`,
  `UserId = NewType("UserId", uuid.UUID)`
- `Annotated` for self-documenting types (constraints, descriptions, examples inline)
- `assert_never` required for exhaustive Enum / Union handling in Python;
  `never` check required in TypeScript
- Every endpoint MUST declare an explicit `response_model=`

### Structured logging

All errors MUST be logged via `loguru` with structured context:

```python
logger.error(
    "export.create_issue failed",
    user_id=user_id,
    item_id=item_id,
    tracker=tracker_type,
    error=str(exc),
)
```

`print()` in production code: **PROHIBITED**.
`logging` stdlib: **PROHIBITED** — use `loguru` exclusively.

### Data integrity

- Hard validation MUST block save when O > M, M > P, or any value ≤ 0;
  inline error appears under the offending cell; auto-save suppressed until valid
- Partial items (not all of O/M/P filled) save with status `incomplete`
- Export idempotency enforced via `estimation_item.tracker_issue_id` (tracker-neutral naming)
- Partial export failures: successful items persisted, failed items reported with detail
- Validation is duplicated: frontend (advisory, UX) and backend (authoritative, enforcement)

### SQL dialect neutrality

All SQL expressions MUST be dialect-neutral via SQLAlchemy Core / ORM.
Raw SQL strings with SQLite-specific syntax: **PROHIBITED**.
All migrations via Alembic exclusively. Manual DDL: **PROHIBITED**.

---

## Principle VI. Mandatory Developer Toolchain

### justfile — the single command runner

**All commands are executed exclusively through `just`.**
Direct invocation of `uvicorn`, `alembic`, `pytest`, `pnpm`, `mypy`, `ruff` outside of
`just` recipes: **PROHIBITED** in documented workflows.

```justfile
# PERT Estimation App — task runner
# Requires: https://github.com/casey/just
# Platform: Windows (cmd.exe)

set shell := ["cmd.exe", "/c"]

# ── backend ────────────────────────────────────────────────────────────────────

# Install backend dependencies
be-sync:
    cd backend && uv sync --all-extras

# Apply all pending DB migrations
be-migrate:
    cd backend && uv run alembic upgrade head

# Start backend dev server (port 8000)
be-dev:
    cd backend && uv run uvicorn src.main:app --reload --host 127.0.0.1 --port 8000

# Run full backend test suite with coverage
be-test:
    cd backend && uv run pytest --cov=src

# Run a single test file
be-test-file file:
    cd backend && uv run pytest {{file}} -v

# mypy strict type-check
be-typecheck:
    cd backend && uv run mypy src/

# ruff lint
be-lint:
    cd backend && uv run ruff check src/

# ruff auto-format
be-format:
    cd backend && uv run ruff format src/

# Generate new Alembic migration  →  just be-revision "describe change"
be-revision msg:
    cd backend && uv run alembic revision --autogenerate -m "{{msg}}"

# Show Alembic migration history
be-history:
    cd backend && uv run alembic history

# ── frontend ───────────────────────────────────────────────────────────────────

# Install frontend dependencies
fe-install:
    cd frontend && pnpm install

# Start Next.js dev server (port 3000)
fe-dev:
    cd frontend && pnpm dev

# Generate TypeScript types from live backend OpenAPI spec
# Backend must be running on :8000 before calling this recipe
fe-generate:
    cd frontend && pnpm openapi-ts

# Run full test suite
fe-test:
    cd frontend && pnpm test

# Run Playwright E2E tests (requires both servers running)
fe-e2e:
    cd frontend && pnpm test:e2e

# TypeScript type-check (tsc --noEmit)
fe-typecheck:
    cd frontend && pnpm typecheck

# ESLint
fe-lint:
    cd frontend && pnpm lint

# Production build
fe-build:
    cd frontend && pnpm build

# ── combined ───────────────────────────────────────────────────────────────────

# Install all dependencies (backend + frontend)
install: be-sync fe-install

# Type-check both backend and frontend
typecheck: be-typecheck fe-typecheck

# Lint both backend and frontend
lint: be-lint fe-lint

# Start both dev servers (Windows: separate terminals required)
dev-be:
    just be-dev

dev-fe:
    just fe-dev

# Run full CI check suite locally before push
ci: be-typecheck be-lint be-test fe-typecheck fe-lint fe-test
```

### Python toolchain

| Tool | Role | Enforcement |
|------|------|-------------|
| `uv` | Package manager + script runner | All installs and runs via `uv` |
| `ruff` | Lint + format (replaces flake8 / black / isort) | pre-commit: `ruff-format` → `ruff-check` |
| `mypy --strict` | Static type checking | pre-commit + `just be-typecheck` |
| `loguru` | Structured logging | All log statements |
| `pre-commit` | Git hook orchestrator | Full chain on every commit |
| `pytest` + `Hypothesis` | Tests + property-based testing | CI must pass |

`mypy --strict` is mandatory. `Any` without an explicit justification comment: **PROHIBITED**.
Pydantic v2 mypy plugin MUST be configured in `pyproject.toml`.

### Pre-commit configuration

Pre-commit runs the **full check suite** on every commit for both backend and frontend.
Speed is not a concern — correctness guarantee is the goal.

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-merge-conflict

  # ── backend ──────────────────────────────────────────────────────────────────
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.4
    hooks:
      - id: ruff-format
        files: ^backend/
      - id: ruff
        files: ^backend/
        args: [--fix]

  - repo: local
    hooks:
      - id: mypy-backend
        name: mypy (backend)
        entry: cmd /c "cd backend && uv run mypy src/"
        language: system
        pass_filenames: false
        files: ^backend/

      # ── frontend ─────────────────────────────────────────────────────────────
      - id: tsc-frontend
        name: tsc (frontend)
        entry: cmd /c "cd frontend && pnpm typecheck"
        language: system
        pass_filenames: false
        files: ^frontend/

      - id: eslint-frontend
        name: eslint (frontend)
        entry: cmd /c "cd frontend && pnpm lint"
        language: system
        pass_filenames: false
        files: ^frontend/
```

### Configuration — single entry point

`backend/src/core/config.py` is the **only** module that reads environment variables.
All other modules receive settings exclusively via FastAPI `Depends()` — never via a
module-level `get_settings()` call.

```python
# PROHIBITED — hidden module-level dependency:
_settings = get_settings()

# REQUIRED — explicit DI:
async def my_endpoint(settings: Annotated[Settings, Depends(get_settings)]) -> ...:
    ...
```

**Frontend env rule:** `NEXT_PUBLIC_*` variables are client-visible (base URL and public
constants only). Everything else is server-side and MUST NEVER be exposed to the browser.

### Git discipline (CRITICAL for AI agents)

Git is the **project memory bank**. Every atomic change MUST be committed immediately.

**REQUIRED for every agent task:**
- Git commit is executed **immediately after every file change**, before moving to the next file
- Commit message format — Conventional Commits:
  `feat(items): add PERT calculation service`
  `fix(export): handle partial failure in tracker adapter`
  `chore(db): rename yt_issue_id to tracker_issue_id`
- Schema changes (Pydantic model + Alembic migration) — separate commit, before implementing logic
- Unrelated changes MUST NOT be grouped into a single commit

**PROHIBITED:**
- Modifying multiple files without intermediate commits
- Changing the data schema without committing the model change first

### Mandatory MCP servers

The agent MUST use available MCP servers for the corresponding task categories:

| MCP server | When to use |
|------------|-------------|
| `git` | Every commit, history review, diff, blame |
| `sequential-thinking` | Before any architectural decision or decomposition |
| `ast-grep` | Code search and refactoring (never plain text grep for code) |
| `youtrack` | Creating / updating tasks, reading requirements |

Ignoring an available MCP server in favour of a less precise tool: **PROHIBITED**.

---

## Principle VII. Identity & Tracker Decoupling

User authentication is **completely decoupled** from tracker connectivity.

### Identity model

- `email` is the sole identity anchor — unique, immutable
- Login: email + password → JWT (15 min access / 30 day refresh); bcrypt for password hashing
- The `User` model contains **no tracker fields**

```python
class User(Base):
    __tablename__ = "users"

    id: Mapped[UserId]
    email: Mapped[str]           # unique — sole identity anchor
    display_name: Mapped[str]
    password_hash: Mapped[str]   # bcrypt
    role: Mapped[Literal["editor", "viewer"]]
    created_at: Mapped[datetime]
    last_seen_at: Mapped[datetime | None]
```

**PROHIBITED:**
- Storing tracker token in the `User` model
- Using an external tracker ID (`yt_user_id`, `jira_account_id`, etc.) as the identity anchor
- Implementing email/password auth as "optional" — it is the primary and only auth method

### TrackerConnection (global system setting)

One record for the entire application. Configured by an administrator via the Settings UI.

```python
class TrackerConnection(Base):
    __tablename__ = "tracker_connections"

    id: Mapped[uuid.UUID]
    tracker_type: Mapped[Literal["youtrack", "jira", "linear", "azure_devops"]]
    base_url: Mapped[str]
    token_encrypted: Mapped[bytes]    # Fernet encryption via ENCRYPTION_KEY
    is_active: Mapped[bool]
    last_verified_at: Mapped[datetime | None]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
```

**PROHIBITED:**
- Per-user tracker token storage
- Duplicating `base_url` between `TrackerConnection` and `Settings`
- More than one active `TrackerConnection` record at a time

**Switching trackers:** update `tracker_type` + `base_url` + `token_encrypted` in the single
`TrackerConnection` record + register the new adapter in DI. Zero changes to business logic.

---

## Principle VIII. Agent Decision Tree (Anti-Hallucination Rules)

This principle exists solely to prevent AI agent hallucinations. It translates architecture
rules into unambiguous binary decisions.

### Structural decision tree

```
Need to mutate system state (write / update / delete)?
  → Create a Command class: CreateSessionCommand(BaseModel)
  → DO NOT put logic in the router

Need a dependency between two services?
  → Define a Protocol in shared/protocols/ or features/{feature}/ports/
  → DO NOT import the concrete class directly

File exceeds 200 lines?
  → STOP. Decompose before writing the next line.
  → Extract logic into a separate module or class

Need an external integration (tracker, email, storage, any third-party API)?
  → Create a Protocol in features/{feature}/ports/
  → Create an adapter in features/{feature}/adapters/
  → DO NOT call external APIs directly from services
```

### Mandatory task execution order

```
1. Read the full spec file for the task
2. Run sequential-thinking MCP to decompose the work
3. Verify: does the proposed solution comply with the constitution?
4. Write tests first (if logic is involved)
5. Write implementation
6. Git commit via git MCP (use ast-grep for pattern verification if needed)
7. Move to the next step only after the commit is recorded
```

### Session Bootstrap Protocol (FIRST action in every session)

Before writing any code, agent MUST read these files in this exact order:

1. `constitution.md` — architectural rules (this file)
2. `specs/001-pert-estimation-sdlc/design.md` — data models, formulas, API contracts
3. `specs/001-pert-estimation-sdlc/design-type-patterns.md` — canonical Python patterns
4. `justfile` — shell syntax and available commands for this OS
5. `specs/001-pert-estimation-sdlc/tasks.md` — current task only (not entire file)

**Reading justfile is NON-NEGOTIABLE** — shell syntax differs between Windows/Linux/Mac.
The justfile is the single source of truth for how commands are run.
DO NOT guess shell syntax. DO NOT use `cd x && y` if justfile uses `cd x; y`.

### Tool Failure Protocol

When any tool call returns an error:

STOP — do not repeat the same call with the same parameters
READ the full error message
IDENTIFY an alternative tool or approach
Maximum 1 retry after changing parameters or tool
If still failing → log to YouTrack MCP and ask user


**PROHIBITED:** calling the same failing tool repeatedly without changing approach.

Example of PROHIBITED behaviour:
create_directory → error: not found
create_directory → error: not found   ← STOP HERE, do not repeat
create_directory → error: not found

Correct behaviour:
create_directory → error: not found
→ read error → switch to mcp__filesystem__create_directory or run_shell_command mkdir


AFTER EVERY PYTHON FILE — NO EXCEPTIONS:

Step 1. Self-check before running tools:
  □ from __future__ import annotations  ← first line of file
  □ every function/method: all parameters annotated
  □ every function/method: return type annotated (including -> None)
  □ no bare list/dict/tuple — only list[T], dict[K, V], tuple[T, ...]
  □ no Optional[T] — only T | None
  □ no Any without # type: ignore[specific-code] with justification comment

Step 2. Run: just be-check-file <path/to/file.py>

Step 3. If errors → fix → repeat Step 2

Step 4. Only after exit code 0 → git commit

DO NOT move to the next file until exit code is 0.


### Prohibited patterns — will be rejected at code review

**1. Business logic in routers:**
```python
# PROHIBITED:
@router.post("/sessions")
async def create_session(db: AsyncSession):
    session = Session(...)   # logic lives in the router
    db.add(session)

# REQUIRED:
@router.post("/sessions", response_model=SessionResponse)
async def create_session(cmd: CreateSessionCommand, svc: SessionService):
    return await svc.create(cmd)
```

**2. Direct adapter import in a service:**
```python
# PROHIBITED:
from app.features.export.adapters.youtrack import YouTrackAdapter

# REQUIRED:
from app.features.export.ports import IssueTrackerPort   # Protocol only
```

**3. Module-level settings call:**
```python
# PROHIBITED:
_settings = get_settings()   # hidden module-level dependency

# REQUIRED:
# Settings injected exclusively via FastAPI Depends()
```

**4. Schema change without specification first:**
```
PROHIBITED: write Alembic migration → then update Pydantic model
REQUIRED:   update Pydantic model → architect review → write migration → commit
```

**5. Solutions outside the specification:**
```
PROHIBITED: use a library, pattern, or approach not present in the constitution or spec file
REQUIRED:   stop and request clarification via YouTrack MCP before proceeding
```

---

## Technology Stack (locked for MVP)

| Layer | Technology | Constraint |
|-------|-----------|------------|
| Frontend framework | Next.js 15 + Server Components | All components are Server Components by default |
| Frontend state | TanStack Query | Client islands only — Server Components handle data fetching |
| Frontend UI | Tailwind CSS + shadcn/ui | No alternative UI libraries in MVP |
| Frontend types | openapi-typescript (generated) | Manual API interfaces: PROHIBITED |
| Frontend package manager | pnpm | npm / yarn / bun: PROHIBITED |
| Backend | FastAPI + Python 3.12 | Minimum Python version: 3.12 |
| ORM | SQLAlchemy 2.0 async + aiosqlite | Alembic for all migrations; raw DDL: PROHIBITED |
| Auth | email / password → JWT | bcrypt for passwords; 15 min access / 30 day refresh |
| Encryption | Fernet (`ENCRYPTION_KEY` from env) | For `TrackerConnection.token_encrypted` |
| Roles | `editor` / `viewer` | No granular permissions beyond two roles in MVP |
| Deployment | Next.js rewrites `/api/*` → FastAPI (`:8000`) | No Nginx; no container orchestration for MVP |
| PDF | xhtml2pdf + Jinja2 | Server-side render; no headless browser; zero system dependencies |
| Command runner | `just` (justfile) | Direct tool invocation outside just: PROHIBITED in documented workflows |

---


## Governance

**Amendment procedure:**

1. Open a PR that modifies this file + the relevant ATAM entry + affected templates
2. Review by the Solution Architect (primary stakeholder)
3. Changes to Principles I–VIII or Technology Stack MUST include an updated trade-off analysis
4. Version MUST be bumped per semantic versioning:
   - MAJOR: removal or incompatible redefinition of a principle
   - MINOR: new principle or section added, or material expansion
   - PATCH: clarification or wording refinement
5. `LAST_AMENDED_DATE` MUST be updated to the merge date in ISO format (YYYY-MM-DD)

**Compliance review — mandatory PR checks:**

| Changed path | Principles to verify |
|-------------|---------------------|
| `features/items/` | I (golden source), III (test coverage) |
| `features/export/` | IV (Port abstraction), V (idempotency + ErrorResponse) |
| Any new service dependency | IV (Protocol required) |
| Any new ID type | V (NewType required) |
| Any commit | VI (toolchain hooks pass, git discipline) |
| New external integration | IV (Port + adapter structure) |
| Schema change | I (Pydantic model first), VI (separate commit) |

**Version**: 1.0.0 | **Ratified**: — | **Last Amended**: —
