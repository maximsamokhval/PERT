# Implementation Plan: PERT Estimation SDLC Tool

**Branch**: `001-pert-estimation-sdlc` | **Date**: 2026-04-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-pert-estimation-sdlc/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Build a PERT estimation tool that allows architects to create estimation sessions, add work items with O/M/P values, see real-time PERT metrics, approve sessions, and export items as YouTrack issues. The system uses backend-authoritative calculations with frontend optimistic updates, separate ExportMapping model for tracker fields, and follows constitution principles for schema-first pipeline and port abstraction.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript/Next.js 15 (frontend)
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 async, Pydantic v2 / TanStack Query, openapi-typescript
**Storage**: SQLite with WAL mode (MVP), Alembic migrations
**Testing**: pytest + Hypothesis (backend), Vitest (frontend), Playwright (E2E)
**Target Platform**: Web application (single-server deployment)
**Project Type**: Full-stack web service with YouTrack integration
**Performance Goals**: <1s metric recalculation on O/M/P change, <5s public link load
**Constraints**: ≤5 concurrent users, ≤100 items per session, JWT auth (15min access / 30day refresh)
**Scale/Scope**: Single-tenant, MVP with YouTrack adapter only

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Schema-First Pipeline | ✅ Clear | Pydantic models → OpenAPI → generated TypeScript types |
| II. Vertical Slice Architecture | ✅ Clear | Features: sessions, items, export, settings |
| III. Test-First & Formula Parity | ✅ Clear | Property-based tests for PERT formulas, 100% coverage |
| IV. Port Abstraction | ✅ Clear | `IssueTrackerPort` protocol, YouTrackAdapter implementation |
| V. Data Contracts & Error Handling | ✅ Clear | ErrorResponse, PartialResultResponse, ErrorCode enum |
| VI. Mandatory Developer Toolchain | ✅ Clear | justfile, pre-commit, git discipline |
| VII. Identity & Tracker Decoupling | ✅ Clear | TrackerConnection separate from User, email/password auth |
| VIII. Agent Decision Tree | ✅ Clear | Command classes, Protocol imports, no business logic in routers |

**GATE RESULT**: ✅ PASS — No violations. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/001-pert-estimation-sdlc/
├── plan.md              # This file
├── research.md          # Phase 0 output (see below)
├── data-model.md        # Phase 1 output (TO BE CREATED)
├── quickstart.md        # Phase 1 output (TO BE CREATED)
├── contracts/           # Phase 1 output
│   ├── items-api.md     # Updated with ExportMapping
│   ├── sessions-api.md  # Updated with ErrorCode enum
│   ├── export-api.md    # Updated with conversion logic
│   └── settings-api.md  # Updated with CON/MDM project fields
└── tasks.md             # Phase 2 output (TO BE CREATED)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── features/
│   │   ├── auth/
│   │   │   ├── routes.py
│   │   │   ├── commands.py
│   │   │   ├── models.py
│   │   │   └── services.py
│   │   ├── sessions/
│   │   │   ├── routes.py
│   │   │   ├── commands.py
│   │   │   ├── models.py
│   │   │   ├── pdf_generator.py
│   │   │   └── services.py
│   │   ├── items/
│   │   │   ├── routes.py
│   │   │   ├── commands.py
│   │   │   ├── models.py
│   │   │   └── services.py
│   │   ├── export/
│   │   │   ├── routes.py
│   │   │   ├── commands.py
│   │   │   ├── ports/
│   │   │   │   └── __init__.py   # IssueTrackerPort protocol
│   │   │   ├── adapters/
│   │   │   │   └── youtrack.py   # YouTrackAdapter
│   │   │   └── services.py
│   │   └── settings/
│   │       ├── routes.py
│   │       ├── commands.py
│   │       ├── models.py
│   │       └── services.py
│   ├── core/
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── security.py
│   │   └── logging.py
│   └── shared/
│       ├── models.py      # ErrorResponse, PartialResultResponse
│       └── types.py       # NewType IDs: SessionId, ItemId, UserId
└── tests/
    ├── contract/
    ├── integration/
    └── unit/

frontend/
└── src/
    ├── features/
    │   ├── auth/
    │   ├── sessions/
    │   ├── items/
    │   ├── export/
    │   └── settings/
    ├── components/
    └── types/             # openapi-typescript generated
```

**Structure Decision**: Vertical slice architecture per Constitution Principle II. Single project structure with backend/ and frontend/ folders.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations to justify. All principles pass.

---

## Phase 0: Research & Unknowns Resolution

**Status**: ✅ COMPLETE — All clarifications resolved via speckit-clarify workflow

### Clarifications Session 2026-04-02 (API Contract Fixes)

| # | Question | Decision | Rationale |
|---|----------|----------|-----------|
| 1 | MappableItemField неповнота | Створити окрему модель `ExportMapping` | Забезпечує чітке розділення між PERT даними та експорт-мапінгом |
| 2 | AUTHENTICATION_ERROR відсутній в ErrorCode | Додати до ErrorCode StrEnum | Узгодженість з export-api.md документацією |
| 3 | Конвертація total_effort → period | `hours_to_period(hours: float) -> str`: `8.8 → "8h 48m"` | Проста utility функція, конвертує decimal minutes |
| 4 | Невалідний focus_factor: 0.75 | Замінити на `0.8` | Найближче валідне значення з Literal[0.5, 0.6, 0.7, 0.8, 0.9, 1.0] |
| 5 | Суперечність optimistic мінімуму | Узгодити items-api.md з data-model (≥1) | PERT формула вимагає додатних значень |

### Updated Contracts

All API contracts updated:
- ✅ `items-api.md` — ExportMapping model added, validation rules fixed (optimistic ≥ 1)
- ✅ `sessions-api.md` — ErrorCode enum added, focus_factor example fixed (0.8)
- ✅ `export-api.md` — Conversion logic section added, AUTHENTICATION_ERROR in error codes
- ✅ `settings-api.md` — CON/MDM project fields from YouTrack

### Spec File Updated

- ✅ `spec.md` — Clarifications section updated with all 5 Q&A pairs

---

## Phase 1: Design & Contracts

**Prerequisites**: ✅ research.md complete

### Deliverables

- [x] **data-model.md** — Entity definitions, Pydantic models, relationships
- [x] **contracts/** — API contracts (already updated via clarification workflow)
- [x] **quickstart.md** — Developer onboarding guide *(deferred to Phase 7 / T083 — write after routes exist)*
- [x] **Agent context update** — Run `.specify/scripts/powershell/update-agent-context.ps1 -AgentType qwen` *(deferred to Phase 7 / T084 — run after stack is finalised)*

### Data Model Preview

**Core Entities**:

1. **Session** — Estimation session with status, focus_factor, hours_per_day
2. **EstimationItem** — O/M/P values, calculated PERT metrics
3. **ExportMapping** — Additional fields for tracker export (work_type, subsystem, assignee, etc.)
4. **TrackerConnection** — Global YouTrack connection settings
5. **ProjectFieldMap** — Field mapping per tracker project

### Constitution Check (Post-Design)

Re-evaluate after data-model.md creation.

---

## Phase 2: Task Breakdown

**Prerequisites**: Phase 1 complete, constitution check passed

**Next Command**: `/speckit.tasks` — Generate task breakdown from this plan

---

## Completion Report

**Branch**: `001-pert-estimation-sdlc`
**Plan Path**: `C:\development\PERT_2_0\specs\001-pert-estimation-sdlc\plan.md`
**Generated Artifacts**:
- ✅ `plan.md` — Implementation plan (this file)
- ✅ `research.md` — Phase 0 findings (integrated into plan.md)
- ✅ `items-api.md` — Updated with ExportMapping
- ✅ `sessions-api.md` — Updated with ErrorCode enum
- ✅ `export-api.md` — Updated with conversion logic
- ✅ `settings-api.md` — Updated with YouTrack project fields
- ✅ `spec.md` — Updated with clarifications

**Status**: Phase 2 planning complete. Ready for `/speckit.tasks`.
