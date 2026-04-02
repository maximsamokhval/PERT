# Research & Decisions: PERT Estimation SDLC Tool

**Feature**: `001-pert-estimation-sdlc`
**Date**: 2026-04-02
**Purpose**: Resolve all technical unknowns and document architectural decisions before Phase 1 design

---

## Technical Decisions

### Decision 1: PERT Calculation Authority

**Decision**: Backend (FastAPI/Python) є єдиним авторитативним джерелом для PERT розрахунків.

**Rationale**:
- Constitution Principle I вимагає Schema-First Pipeline з backend як authoritative source
- Уникнення formula drift між JS frontend та Python backend
- Frontend може мати optimistic preview для UX, але остаточні значення завжди синхронізуються з backend

**Alternatives Considered**:
- Client-side calculations only: відхилено через ризик不一致 та відсутність централізованої валідації
- Dual authority: відхилено через неможливість гарантувати parity

---

### Decision 2: Database Strategy

**Decision**: SQLite з WAL mode для MVP з міграціями через Alembic.

**Rationale**:
- Constitution Principle II вимагає SQLite для MVP (≤ 5 concurrent users, single-tenant)
- SQLAlchemy 2.0 async забезпечує dialect neutrality
- Alembic автоматизує міграції з autogenerate

**Alternatives Considered**:
- PostgreSQL: відкладено до trigger SP-01 (> 3 concurrent editors або p95 lock wait > 100ms)
- Direct SQL: заборонено Constitution Principle V

---

### Decision 3: Issue Tracker Integration

**Decision**: `IssueTrackerPort` Protocol з YouTrackAdapter як першою реалізацією.

**Rationale**:
- Constitution Principle IV вимагає Port abstraction для всіх зовнішніх залежностей
- DI дозволяє замінити tracker без змін бізнес-логіки
- Target switch cost < 2 person-days

**Alternatives Considered**:
- Direct YouTrack API calls у services: відхилено (порушує Principle IV)
- Multiple trackers одночасно: відкладено до MVP (тільки YouTrack спочатку)

---

### Decision 4: Authentication Strategy

**Decision**: Email/password auth з JWT tokens (15 min access / 30 day refresh).

**Rationale**:
- Constitution Principle VII вимагає email як identity anchor
- bcrypt для password hashing
- Refresh tokens для тривалих сесій без повторного логіну

**Alternatives Considered**:
- OAuth 2.0 only: відхилено для MVP (додаткова складність)
- Tokenless: відхилено (вимагається для персоналізації сесій)

---

### Decision 5: Real-time Updates Strategy

**Decision**: Auto-save з debounce ≤ 2s, optimistic UI updates з backend sync.

**Rationale**:
- Spec вимагає "миттєве оновлення метрик без перезавантаження"
- Constitution Principle I вимагає backend як golden source
- Debalance між UX (швидкість) та consistency (backend авторитет)

**Alternatives Considered**:
- WebSocket real-time: відхилено для MVP (додаткова складність)
- Manual save only: відхилено (погіршує UX)

---

### Decision 6: PDF Generation Approach

**Decision**: xhtml2pdf + Jinja2 для server-side PDF генерації.

**Rationale**:
- Constitution Technology Stack锁定 xhtml2pdf для MVP
- Server-side render уникає headless browser залежностей
- Zero system dependencies (порівняно з Puppeteer/Playwright)

**Alternatives Considered**:
- Headless Chrome (Puppeteer): відхилено (system dependencies, складність deployment)
- Client-side pdf-generation: відхилено (consistency issues)

---

### Decision 7: Focus Factor Implementation

**Decision**: Focus Factor (FF) та hours_per_day є session-level параметрами з default FF=0.8, hours_per_day=8.

**Rationale**:
- Spec вимагає розрахунок тривалості з урахуванням продуктивності
- FF models reality that engineers are not 100% productive
- Session-level дозволяє different teams з different productivity

**Alternatives Considered**:
- Global system setting: відхилено (менше гнучкості)
- Item-level FF: відхилено (over-engineering для MVP)

---

### Decision 8: Concurrent Editing Strategy

**Decision**: Optimistic locking з попередженням про конфлікт при збереженні.

**Rationale**:
- Spec clarification вимагає обробки concurrent edits
- MVP ≤ 5 concurrent users робить pessimistic locking overkill
- User-friendly conflict resolution

**Alternatives Considered**:
- Pessimistic locking (session-level lock): відхилено (friction для MVP)
- CRDTs: відхилено (over-engineering)
- Last-write-wins: відхилено (data loss risk)

---

### Decision 9: Export Idempotency

**Decision**: `estimation_item.tracker_issue_id` як унікальний ідентифікатор для idempotency.

**Rationale**:
- Constitution Principle V вимагає export idempotency
- Tracker-neutral naming (не `yt_issue_id`)
- Partial export failures обробляються з 207 Multi-Status

**Alternatives Considered**:
- External ID mapping table: відхилено (додаткова складність)
- No idempotency: відхилено (duplicate tasks risk)

---

### Decision 10: Session Limit Enforcement

**Decision**: Soft cap 50 items, hard cap 100 items з virtual list pagination.

**Rationale**:
- Spec Assumptions вказують 100 items maximum
- Soft cap попереджає користувача до досягнення hard limit
- Virtual list забезпечує продуктивність при великій кількості елементів

**Alternatives Considered**:
- No limit: відхилено (performance degradation)
- Hard cap only: відхилено (user frustration)

---

## Open Questions (Resolved)

| Question | Resolution |
|----------|------------|
| Який метод автентифікації? | Email/password + JWT (15min/30d) |
| Чи потрібен audit log? | Ні, лише поточний стан |
| Як обробляти concurrent edits? | Optimistic locking з conflict warning |
| Яка стратегія retry для YouTrack? | Одразу помилка, manual retry |
| Який ліміт елементів? | Soft 50, hard 100 |

---

## Technology Summary

| Component | Technology | Version |
|-----------|-----------|---------|
| Backend Framework | FastAPI | latest |
| ORM | SQLAlchemy + async | 2.0+ |
| DB | SQLite | WAL mode |
| Migrations | Alembic | latest |
| Validation | Pydantic | v2 |
| Frontend Framework | Next.js | 15 (App Router) |
| Frontend State | TanStack Query | latest |
| UI Components | shadcn/ui + Tailwind | latest |
| Package Manager (FE) | pnpm | latest |
| Auth | JWT | bcrypt hashing |
| Encryption | Fernet | for tracker tokens |
| PDF | xhtml2pdf + Jinja2 | latest |
| Testing (BE) | pytest + Hypothesis | latest |
| Logging | loguru | latest |
| Task Runner | just | latest |
