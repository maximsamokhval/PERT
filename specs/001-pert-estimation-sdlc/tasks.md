# Tasks: PERT Estimation SDLC Tool

**Input**: Design documents from `/specs/001-pert-estimation-sdlc/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, contracts/

**Tests**: Test tasks are included per Constitution Principle III (TDD mandatory — 100% PERT formula coverage, property-based tests, E2E critical path). Merging without CI passing is prohibited.

## Document Authority Hierarchy

When field names, types, or values conflict between documents — follow this order:
constitution.md         ← highest authority
design.md               ← data models, formulas, field names
design-type-patterns.md ← Python patterns
data-model.md           ← supporting detail only
research.md             ← context only, NOT authoritative for field names
tasks.md                ← implementation order only

# Tasks: PERT Estimation SDLC Tool

## ⛔ Universal Completion Protocol — applies to EVERY task

Before marking ANY task `[x]`, execute in order:
1. `git add <changed_file_path>`
2. `git commit -m "type(scope): description"`

One file = one commit. No batching. No exceptions.
This rule overrides task-level instructions.


**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- Paths shown below assume backend/frontend structure per plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create backend project structure: backend/src/features/{sessions,items,export,settings,auth}/, backend/src/core/, backend/src/shared/
- [x] T002 Create frontend project structure: frontend/src/features/{sessions,items,export,settings,auth}/, frontend/src/components/, frontend/src/types/
- [x] T003 [P] Initialize backend with FastAPI, SQLAlchemy 2.0 async, Pydantic v2, aiosqlite in backend/pyproject.toml
- [x] T004 [P] Initialize frontend with Next.js 15, TanStack Query, Tailwind CSS, shadcn/ui in frontend/package.json
- [x] T005 [P] Configure backend linting and formatting (ruff, mypy --strict) in backend/pyproject.toml
- [x] T006 [P] Configure frontend linting and formatting (ESLint, Prettier) in frontend/package.json
- [x] T007 Create justfile with all recipes: be-sync, be-dev, be-test, be-migrate, fe-install, fe-dev, fe-generate, ci
- [x] T008 Setup .pre-commit-config.yaml with ruff-format, ruff-check, mypy-backend, tsc-frontend, eslint-frontend

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T009 [P] Create NewType IDs in backend/src/shared/types.py: SessionId, ItemId, UserId, ExportMappingId
- [x] T010 [P] Create ErrorResponse and PartialResultResponse models in backend/src/shared/errors.py per Constitution Principle V:
  - ErrorResponse: code (str), message (str), detail (str | None), request_id (str UUID for log correlation)
  - PartialResultResponse: succeeded (list[ItemResult]), failed (list[FailedItemResult]), total (int)
- [x] T011 [P] Create ErrorCode StrEnum in backend/src/shared/enums.py: VALIDATION_ERROR, NOT_FOUND, UNAUTHORIZED, FORBIDDEN, CONFLICT, AUTHENTICATION_ERROR
- [x] T012 [P] Implement configuration management in backend/src/core/config.py: Settings with ENCRYPTION_KEY, database URL, JWT settings
- [x] T013 [P] Implement database connection in backend/src/core/db.py: AsyncSession, engine with WAL mode for SQLite
- [x] T014 [P] Implement JWT authentication middleware in backend/src/core/security.py: bcrypt password hashing, access/refresh tokens
- [x] T015 [P] Create base User model in backend/src/features/auth/models.py: email, display_name, password_hash, role (editor/viewer), last_seen_at (datetime | None)
- [x] T016 [P] Implement AuthService in backend/src/features/auth/services.py: login, register, token refresh
- [x] T017 [P] Create auth routes in backend/src/features/auth/routes.py: POST /api/auth/login, POST /api/auth/register, POST /api/auth/refresh, GET /api/auth/me
- [x] T018 [P] Setup Alembic migrations framework in backend/alembic/: env.py, script.py.mako, initial migration
- [x] T019 [P] Configure loguru structured logging in backend/src/core/logging.py
- [x] T020 [P] Create frontend API client in frontend/src/lib/api.ts: fetch wrapper with JWT auth headers, automatic access-token injection, and silent refresh via refresh-token on 401
- [x] T021 [P] Create LoginPage in frontend/src/app/login/page.tsx: email/password form, calls POST /api/auth/login, stores JWT in httpOnly cookie via Server Action
- [x] T021a [P] Create RegisterPage in frontend/src/app/register/page.tsx: email/display_name/password form, calls POST /api/auth/register
- [x] T021b [P] Implement useAuth hook in frontend/src/features/auth/hooks/use-auth.ts: TanStack Query wrapper for current user, login, logout, register
- [x] T021c [P] Create auth Server Actions in frontend/src/features/auth/actions/auth.ts: login, logout, register — handle JWT cookie lifecycle
- [x] T022 [P] Create base Command/Service dependency injection pattern in backend/src/core/db.py: get_db dependency for FastAPI Depends()
- [x] T023 [P] Create shared test fixtures in backend/tests/fixtures/__init__.py: pytest fixtures for db session, test client, auth tokens
- [x] T024 [P] Create PERT test vectors fixture in backend/tests/fixtures/pert_test_vectors.json: 1000+ test cases for property-based testing (consumed by T090/T092)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Створення та редагування сесії оцінювання (Priority: P1) 🎯 MVP

**Goal**: Architect can create estimation sessions, add/edit/delete work items with O/M/P values, see real-time PERT metrics recalculated instantly

**Independent Test**: Create session → add one item with O=2, M=4, P=8 → verify t(E)=4.33, spread=6, σ=1 displayed without page reload

### Test-First Prerequisites (Constitution Principle III)

- [x] T024a [P] [US1] Write property-based tests for PERT formulas in backend/tests/unit/test_pert_calculations.py using Hypothesis: 1000+ random inputs validating against Canonical PERT Formula Reference
- [x] T024b [P] [US1] Create shared test vectors fixture in backend/tests/fixtures/pert_test_vectors.json: 1000+ test cases for Python/JS parity (consumed by T029, T044, T092)
- [x] T024c [P] [US1] Write Vitest PERT formula parity test suite in frontend/tests/unit/pert-parity.test.ts: consumes T024b, verifies frontend/src/features/items/utils/pert-calc.ts produces identical results for all test vectors

### Implementation for User Story 1

- [ ] T025 [P] [US1] Create Session SQLAlchemy model in backend/src/features/sessions/models.py: id, user_id, title, description, status (draft/approved), focus_factor (Literal[0.5,0.6,0.7,0.8,0.9,1.0]), hours_per_day, contingency_factor k (Literal[0.05,0.1,0.15,0.2], default 0.1), created_at, updated_at, approved_at — Note: spread_threshold added in T046
- [ ] T026 [P] [US1] Create EstimationItem SQLAlchemy model in backend/src/features/items/models.py: id, session_id, title, description, optimistic, most_likely, pessimistic, t_expected, spread, sigma, variance, hidden_reserve, total_effort, duration_days, tracker_issue_id, export_status, created_at, updated_at
- [ ] T027 [P] [US1] Create Pydantic schemas for Session in backend/src/features/sessions/schemas.py: SessionCreate, SessionUpdate, SessionRead, SessionListRead — include contingency_factor: Literal[0.05, 0.1, 0.15, 0.2] = 0.1 in Create/Update/Read schemas
- [ ] T028 [P] [US1] Create Pydantic schemas for Item in backend/src/features/items/schemas.py: ItemCreate, ItemUpdate, ItemRead, ItemListRead with validation O ≥ 1, M ≥ O, P ≥ M, all integers ≥ 1 (no decimals — per FR-013 and Canonical PERT Formula Reference); ItemRead MUST include duration_days: float (3 decimal precision) per Constitution Principle I; validation via shared test vectors (T091/T092)
- [ ] T028-validate [P] [US1] Add backend validation in ItemCreate schema: O ≥ 1, M ≥ O, P ≥ M, all integers — reject with VALIDATION_ERROR if constraints violated (per FR-013 and Canonical PERT Formula Reference)
- [ ] T028a [P] [US1] Create session Command classes in backend/src/features/sessions/commands.py: CreateSessionCommand, UpdateSessionCommand, ApproveSessionCommand, CloneSessionCommand (all BaseModel, used by routes to delegate to SessionService)
- [ ] T028b [P] [US1] Create item Command classes in backend/src/features/items/commands.py: CreateItemCommand, UpdateItemCommand, DeleteItemCommand, BatchUpdateItemsCommand (all BaseModel)
- [ ] T029_test [US1] Write unit tests FIRST for PERT calculation in backend/tests/unit/test_pert_calculations.py: verify all formulas using spec verification example (O=2, M=4, P=8, k=0.1, FF=0.8, hours_per_day=8 → t(E)=4.333, spread=6, σ=1.0, V=1.0, R=0.6, TE=4.933, D=0.772) — **TDD RED phase**: (1) Write test with expected values → (2) Run test and verify it FAILS (RED) → (3) Implement T029 → (4) Run test and verify it PASSES (GREEN). Test must fail before T029 implementation proceeds. All metrics MUST assert 3 decimal precision.
- [ ] T029 [US1] Implement PERT calculation service in backend/src/features/items/services.py: calculate_pert_metrics(O, M, P, k, FF, hours_per_day) → t_expected, spread, sigma, variance, hidden_reserve, total_effort, duration_days — all floats with 3 decimal precision; k sourced from session.contingency_factor; duration_days = total_effort / (FF × hours_per_day)
- [ ] T030 [US1] Implement SessionService in backend/src/features/sessions/services.py: create, get, update, delete, approve, clone with auto-save
- [ ] T031 [US1] Implement ItemService in backend/src/features/items/services.py: create, get, update, delete with optimistic locking (updated_at comparison)
- [ ] T032_test [US1] Write integration test stubs (TDD RED) for session routes in backend/tests/integration/test_sessions.py: create/get/update/delete/approve/clone endpoints — test file must exist before T032 routes are written
- [ ] T032 [US1] Create session routes in backend/src/features/sessions/routes.py: POST/GET/PATCH/DELETE /api/sessions/{id}
- [ ] T033_test [US1] Write integration test stubs (TDD RED) for item routes in backend/tests/integration/test_items.py: create/get/update/delete/batch endpoints — test file must exist before T033 routes are written
- [ ] T033 [US1] Create item routes in backend/src/features/items/routes.py: POST/GET/PATCH/DELETE /api/sessions/{session_id}/items/{item_id}
- [ ] T033a [US1] Generate TypeScript types from OpenAPI: run `just fe-generate` to create frontend/src/types/api.ts (backend must be running on :8000 with routes from T032/T033)
- [ ] T034 [US1] Implement batch update endpoint in backend/src/features/items/routes.py: PATCH /api/sessions/{session_id}/items/batch with 207 Multi-Status
- [ ] T035 [US1] Add session aggregates calculation in backend/src/features/sessions/services.py: total_effort, duration_days, buffer_95, sigma_total — pass session.contingency_factor as k to calculate_pert_metrics for each item; session duration_days = Σ TE / (FF × hours_per_day) with 3 decimal precision
- [ ] T035a [US1] Implement B₉₅ (95% Contingency Buffer) calculation in backend/src/features/sessions/services.py: B₉₅ = 1.645 × σ_tot where σ_tot = √(ΣV) — MUST use 3 decimal precision; verify via shared test vectors (T091)
- [ ] T036 [US1] Create SessionFeature folder in frontend/src/features/sessions/: components/, hooks/, actions/
- [ ] T037 [US1] Create SessionForm component in frontend/src/features/sessions/components/session-form.tsx: title, description, focus_factor inputs
- [ ] T038 [US1] Create ItemForm component in frontend/src/features/sessions/components/item-form.tsx: O/M/P integer inputs (≥ 1, no decimals) with inline validation O ≤ M ≤ P (per FR-013)
- [ ] T039 [US1] Create SessionList component in frontend/src/features/sessions/components/session-list.tsx: display all sessions with status
- [ ] T040 [US1] Implement useSession hook in frontend/src/features/sessions/hooks/use-session.ts: TanStack Query for session CRUD
- [ ] T041 [US1] Implement useItems hook in frontend/src/features/sessions/hooks/use-items.ts: TanStack Query for item CRUD with optimistic updates
- [ ] T042 [US1] Create Server Action for session creation in frontend/src/features/sessions/actions/create-session.ts
- [ ] T043 [US1] Create Server Action for item update in frontend/src/features/sessions/actions/update-item.ts with debounced auto-save
- [ ] T044 [P] [US1] Implement frontend optimistic PERT calculation utility in frontend/src/features/items/utils/pert-calc.ts: mirrors backend formulas (t_expected, spread, sigma, hidden_reserve, total_effort, duration_days) using session.contingency_factor as k — **NON-AUTHORITATIVE UI PREVIEW ONLY per Constitution Principle I**; **MUST re-sync from backend response on every save (debounce ≤ 2s)**; results must match shared test vectors (T091/T092) with 3 decimal precision; backend response is the single source of truth
- [ ] T045 [US1] Implement PERT metrics display component in frontend/src/features/sessions/components/metrics-display.tsx: t_expected, spread, sigma, total_effort, duration_days — all displayed with 3 decimal precision
**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Візуальна ідентифікація елементів з високим розмахом (Priority: P2)

**Goal**: System visually highlights items with high spread (spread > threshold), architect can quickly identify and review them

**Independent Test**: Create two items: one with spread=2 (O=3,M=4,P=5), one with spread=9 (O=1,M=4,P=10) → verify second item is highlighted

### Implementation for User Story 2

- [ ] T046 [P] [US2] Add spread_threshold configuration to Session model in backend/src/features/sessions/models.py (default: 5)
- [ ] T047 [US2] Add is_high_spread bool field to ItemRead schema in backend/src/features/items/schemas.py (plain field, not a computed property); ItemService.get_items(session_id) reads session.spread_threshold and sets is_high_spread = item.spread > session.spread_threshold on each ItemRead before returning
- [ ] T048 [US2] Update item routes in backend/src/features/items/routes.py: is_high_spread is populated by ItemService (service layer per T047), not by schema; verify all list/detail endpoints return is_high_spread in the response
- [ ] T049 [US2] Create HighSpreadBadge component in frontend/src/features/items/components/high-spread-badge.tsx: visual indicator (color/icon)
- [ ] T050 [US2] Update ItemList component in frontend/src/features/items/components/item-list.tsx: apply highlight styling for is_high_spread items
- [ ] T051 [US2] Add spread filter in frontend/src/features/items/components/item-filters.tsx: show all / show high spread only
- [ ] T051a [US1] Implement optimistic locking conflict resolution UI in frontend/src/features/sessions/components/session-conflict-dialog.tsx: when backend returns 409 Conflict (updated_at mismatch), show dialog with "Your changes vs Server changes" comparison and options: (1) Reload server version, (2) Force overwrite with warning

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Схвалення сесії та експорт задач у YouTrack (Priority: P3)

**Goal**: Architect approves session (draft → approved), system exports items as YouTrack issues, records tracker_issue_id back to items

**Independent Test**: Configure YouTrack connection → create session with 2 items → approve → verify issues created in YouTrack, IDs saved to items

### Implementation for User Story 3

- [ ] T052 [P] [US3] Create ExportMapping SQLAlchemy model in backend/src/features/export/models.py: item_id (FK), work_type, subsystem, assignee, analyst, developer, priority, start_date, lead_time
- [ ] T053 [P] [US3] Create TrackerConnection SQLAlchemy model in backend/src/features/settings/models.py: tracker_type (Literal["youtrack","jira","linear","azure_devops"]), base_url, token_encrypted (Fernet bytes), is_active, last_verified_at, created_at, updated_at — **Add unique constraint to ensure only one active connection at a time** (Constitution Principle VII)
- [ ] T053a [P] [US3] Add partial unique index in Alembic migration: `CREATE UNIQUE INDEX idx_one_active_connection ON tracker_connections (is_active) WHERE is_active = TRUE` — ensures only one active tracker connection at a time (Constitution Principle VII)
- [ ] T054 [P] [US3] Create ProjectFieldMap SQLAlchemy model in backend/src/features/settings/models.py: project_id, mappings (JSON)
- [ ] T055 [P] [US3] Create Pydantic schemas for ExportMapping in backend/src/features/export/schemas.py: ExportMappingCreate, ExportMappingRead
- [ ] T056 [P] [US3] Create Pydantic schemas for Settings in backend/src/features/settings/schemas.py: TrackerConfig, ProjectFieldMapRead
- [ ] T056a [P] [US3] Create export Command classes in backend/src/features/export/commands.py: ExportSessionCommand, RetryExportCommand (all BaseModel, used by export routes to delegate to ExportService)
- [ ] T056b [P] [US3] Create settings Command classes in backend/src/features/settings/commands.py: ConfigureTrackerCommand, ConfigureFieldMappingCommand (all BaseModel)
- [ ] T057 [P] [US3] Define IssueTrackerPort Protocol in backend/src/features/export/ports/__init__.py: test_connection, list_projects, get_project_fields, create_issue
- [ ] T058 [P] [US3] Implement YouTrackAdapter in backend/src/features/export/adapters/youtrack.py: IssueTrackerPort implementation with Fernet encryption
- [ ] T059 [US3] Implement hours_to_period utility in backend/src/features/export/utils.py: float hours → "Xh Ym" format (e.g., 8.8 → "8h 48m")
- [ ] T060 [US3] Implement ExportService in backend/src/features/export/services.py: export_items, retry_failed, get_preview with IssueTrackerPort DI
- [ ] T061 [US3] Implement SettingsService in backend/src/features/settings/services.py: configure_tracker, test_tracker, list_projects, configure_field_mapping
- [ ] T062 [US3] Create export routes in backend/src/features/export/routes.py: POST /api/sessions/{id}/export, POST /api/sessions/{id}/export/retry, GET /api/sessions/{id}/export/preview
- [ ] T063 [US3] Create settings routes in backend/src/features/settings/routes.py: GET/POST/DELETE /api/settings/tracker, GET/POST /api/settings/tracker/projects/{id}/mapping
- [ ] T064 [US3] Add session approval endpoint in backend/src/features/sessions/routes.py: POST /api/sessions/{id}/approve with validation (must have items)
- [ ] T065 [US3] Add session clone endpoint in backend/src/features/sessions/routes.py: POST /api/sessions/{id}/clone with tracker_issue_id reset
- [ ] T066 [US3] Create CloneSessionButton in frontend/src/features/sessions/components/session-actions.tsx: visible on approved sessions, calls POST /api/sessions/{id}/clone and redirects to new draft; also shows informational message (not error) when architect tries to revert approved→draft, suggesting clone as the alternative
- [ ] T067 [US3] Create ExportFeature folder in frontend/src/features/export/: components/, hooks/, actions/
- [ ] T068 [US3] Create SettingsFeature folder in frontend/src/features/settings/: components/, hooks/, actions/
- [ ] T069 [US3] Create TrackerConfigForm component in frontend/src/features/settings/components/tracker-config-form.tsx: base_url, token inputs
- [ ] T070 [US3] Create ProjectMappingForm component in frontend/src/features/settings/components/project-mapping-form.tsx: field mapping UI
- [ ] T071 [US3] Create ExportPreview component in frontend/src/features/export/components/export-preview.tsx: show mapped fields before export
- [ ] T072 [US3] Create ExportResults component in frontend/src/features/export/components/export-results.tsx: display 207 Multi-Status results (success/failed)
- [ ] T073 [US3] Implement useExport hook in frontend/src/features/export/hooks/use-export.ts: TanStack Query for export operations
- [ ] T074 [US3] Implement useSettings hook in frontend/src/features/settings/hooks/use-settings.ts: TanStack Query for tracker configuration
- [ ] T075 [US3] Create Server Action for export in frontend/src/features/export/actions/export-session.ts
- [ ] T076 [US3] Add approve button in frontend/src/features/sessions/components/session-actions.tsx: changes status to approved, locks editing

**Checkpoint**: At this point, User Stories 1, 2, and 3 should all work independently

---

## Phase 6: User Story 4 - Генерація PDF та публічне посилання (Priority: P4)

**Goal**: Architect can generate PDF report or create public read-only link for client viewing without authentication

**Independent Test**: Create approved session → generate PDF → verify file contains all items/metrics; create public link → open in incognito → verify read-only access

### Implementation for User Story 4

- [ ] T077 [P] [US4] Create PublicSessionLink SQLAlchemy model in backend/src/features/sessions/models.py: session_id (FK), token (unique), expires_at, is_active
- [ ] T078 [P] [US4] Create Pydantic schemas for public links in backend/src/features/sessions/schemas.py: PublicLinkCreate, PublicLinkRead
- [ ] T079 [P] [US4] Create Jinja2 PDF template in backend/src/features/sessions/templates/pdf_report.html: session header (title, date, status), items table (O, M, P, t(E), spread, σ, R, TE per item), session totals (Σ TE, D_session, B₉₅), print-friendly CSS
- [ ] T080 [US4] Implement PDF generation service in backend/src/features/sessions/pdf_generator.py: xhtml2pdf + Jinja2 template (T079), include all items/metrics
- [ ] T081 [US4] Create public session routes in backend/src/features/sessions/routes.py: POST /api/sessions/{id}/public-link, GET /api/public/sessions/{token}
- [ ] T082 [US4] Create PDF generation endpoint in backend/src/features/sessions/routes.py: GET /api/sessions/{id}/pdf (authenticated, returns PDF file)
- [ ] T083 [US4] Implement public session reader in backend/src/features/sessions/services.py: get_public_session(token) with expiry check
- [ ] T084 [US4] Create PublicSessionView page in frontend/src/app/public/sessions/[token]/page.tsx: read-only view with no auth required
- [ ] T085 [US4] Create PDFDownloadButton component in frontend/src/features/sessions/components/pdf-download-button.tsx: calls /api/sessions/{id}/pdf
- [ ] T086 [US4] Create PublicLinkGenerator component in frontend/src/features/sessions/components/public-link-generator.tsx: create/copy public link
- [ ] T087 [US4] Add public link display in frontend/src/features/sessions/components/session-actions.tsx: show active public link status

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T088 [P] Create quickstart.md in specs/001-pert-estimation-sdlc/quickstart.md: developer onboarding guide with setup instructions *(plan.md Phase 1 Design deliverable — deferred here intentionally; write after all routes exist so setup steps are accurate)*
- [ ] T089 [P] Run `.specify/scripts/powershell/update-agent-context.ps1 -AgentType qwen` to update agent context with new technologies *(plan.md Phase 1 Design deliverable — deferred here intentionally; run after stack is finalised)*
- [ ] T090 [RENUMBERED → T024a] Moved to Phase 3 (Test-First Prerequisites) per Constitution Principle III
- [ ] T091 [RENUMBERED → T024b] Moved to Phase 3 (Test-First Prerequisites) per Constitution Principle III
- [ ] T092 [RENUMBERED → T024c] Moved to Phase 3 (Test-First Prerequisites) per Constitution Principle III
- [ ] T093 [P] Write Vitest unit tests for frontend hooks and components in frontend/tests/unit/: useSession, useItems, useExport hooks; SessionForm, ItemForm, MetricsDisplay component rendering
- [ ] T094 [P] Finalize integration test coverage in backend/tests/integration/test_sessions.py (extends T032_test stubs): add approval, clone, aggregate calculation, and error path scenarios
- [ ] T095 [P] Finalize integration test coverage in backend/tests/integration/test_items.py (extends T033_test stubs): add batch update, optimistic locking conflict, is_high_spread, and error path scenarios
- [ ] T096 [P] Write contract tests for API endpoints in backend/tests/contract/test_api_contracts.py
- [ ] T097 [P] Write E2E tests with Playwright in frontend/tests/e2e/test_critical_path.py: login → create session → add item → approve → export
- [ ] T098 Documentation updates in README.md: feature description, architecture diagram, API documentation links
- [ ] T099 Code cleanup and refactoring: ensure all files ≤ 200 lines per constitution
- [ ] T100 Security hardening: review all SQL queries for injection, validate all user inputs, secure JWT handling
- [ ] T101 Performance optimization: add database indexes on session_id, user_id; optimize aggregate queries
- [ ] T102 [P] SC-002 performance assertion: Playwright test in frontend/tests/e2e/test_perf_sc002.py — measure time from O/M/P input change to metrics DOM update; assert < 1 000 ms (SC-002)
- [ ] T103 [P] SC-004 performance assertion: Playwright test in frontend/tests/e2e/test_perf_sc004.py — measure full page load of public session link with no auth; assert < 5 000 ms (SC-004)
- [ ] T103a [P] SC-003 validation test: Backend integration test in backend/tests/integration/test_export.py — simulate export of 100+ items with 5% mock failures; assert success rate ≥ 95% and failed items returned in PartialResultResponse.failed with error codes (SC-003)
- [ ] T103b [P] SC-005 validation test: Playwright test in frontend/tests/e2e/test_sc005.py — user identifies high spread items within 10 seconds; assert visual highlight visible and identifiable (SC-005)
- [ ] T104 Run full CI check: `just ci` (be-typecheck, be-lint, be-test, fe-typecheck, fe-lint, fe-test)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1 (uses same models)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on Session/Item models from US1
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Depends on Session model from US1

### Within Each User Story

- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 1 (Setup)**: T003-T008 can all run in parallel (different files)
- **Phase 2 (Foundational)**: T009-T021c can mostly run in parallel (different modules)
- **Phase 3 (US1)**: T025-T028b (models/schemas/commands) can run in parallel; T036-T045 (frontend) can run in parallel after backend ready; T033a runs after T032/T033
- **Across Stories**: After Phase 2, US1, US2, US3, US4 can proceed in parallel with different developers

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "Create Session SQLAlchemy model in backend/src/features/sessions/models.py"
Task: "Create EstimationItem SQLAlchemy model in backend/src/features/items/models.py"
Task: "Create Pydantic schemas for Session in backend/src/features/sessions/schemas.py"
Task: "Create Pydantic schemas for Item in backend/src/features/items/schemas.py"

# Launch all frontend components together (after backend ready):
Task: "Create SessionForm component in frontend/src/features/sessions/components/session-form.tsx"
Task: "Create ItemForm component in frontend/src/features/sessions/components/item-form.tsx"
Task: "Create SessionList component in frontend/src/features/sessions/components/session-list.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
   - Create session → add item with O/M/P → verify PERT metrics
   - Edit item → verify metrics recalculate instantly
   - Delete item → verify aggregates update
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (high spread highlighting)
4. Add User Story 3 → Test independently → Deploy/Demo (YouTrack export)
5. Add User Story 4 → Test independently → Deploy/Demo (PDF + public links)
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (core PERT functionality)
   - Developer B: User Story 2 (spread highlighting)
   - Developer C: User Story 3 (YouTrack integration)
   - Developer D: User Story 4 (PDF + public links)
3. Stories complete and integrate independently

---

## Task Summary

| Phase | Description | Task Count |
|-------|-------------|------------|
| Phase 1 | Setup | 8 tasks |
| Phase 2 | Foundational | 16 tasks |
| Phase 3 | User Story 1 (P1 - MVP) | 27 tasks |
| Phase 4 | User Story 2 (P2) | 6 tasks |
| Phase 5 | User Story 3 (P3) | 27 tasks |
| Phase 6 | User Story 4 (P4) | 11 tasks |
| Phase 7 | Polish & Cross-Cutting | 17 tasks |
| **Total** | | **112 tasks** |

### Task Count per User Story

- **US1**: 27 tasks (T022–T041, T025a, T025b, T026_test, T029_test, T030_test, T030a, T040a)
- **US2**: 6 tasks (T043–T048)
- **US3**: 27 tasks (T049–T072, T053a, T053b, T062f)
- **US4**: 11 tasks (T073–T082, T075a)

### Independent Test Criteria

- **US1**: Create session → add item (O=2,M=4,P=8) → verify t(E)=4.33, spread=6 displayed
- **US2**: Create items with different spreads → verify high spread (>5) highlighted
- **US3**: Configure YouTrack → approve session → verify issues created, IDs saved
- **US4**: Generate PDF → verify content; create public link → verify read-only access

### Suggested MVP Scope

**Minimum**: Phase 1 + Phase 2 + Phase 3 (User Story 1 only) = 51 tasks

This delivers:
- Session CRUD with auto-save
- Item CRUD with O/M/P inputs
- Real-time PERT metric calculations
- Visual display of metrics
- Basic session management

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
