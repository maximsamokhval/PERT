# Data Model: PERT Estimation SDLC Tool

**Feature**: `001-pert-estimation-sdlc`
**Date**: 2026-04-02
**Source**: spec.md + research.md + architecture decisions Q1–Q16

---

## Design Decisions Summary

| # | Decision | Value |
|---|----------|-------|
| Q1 | O/M/P type | `int`, min=1, max=999 |
| Q2 | Calculated fields precision | 2 decimal places (storage = display) |
| Q3 | pessimistic max | 999 hours |
| Q4 | O ≤ M ≤ P enforcement | `@model_validator(mode='after')` only |
| Q5 | title min length | 3 characters |
| Q6 | description nullability | `str` only (empty `""` allowed, `None` forbidden) |
| Q7 | password rules | min 8 characters |
| Q8 | email type | `pydantic.EmailStr` |
| Q9 | datetime type | `pydantic.AwareDatetime` (UTC required) |
| Q10 | focus_factor | `Literal[0.5, 0.6, 0.7, 0.8, 0.9, 1.0]` |
| Q11 | calculated fields | `ItemMetrics` composition model |
| Q12 | ID types | `NewType` + `UUID4` (v4 validated) |
| Q13 | enums | `StrEnum` (Python 3.11+) |
| Q14 | model_config | `strict=True, frozen=True, populate_by_name=True, use_enum_values=True` |
| Q15 | hours_per_day | `int`, gt=0, le=12 |
| Q16 | tracker_issue_id pattern | `r"^[A-Z0-9]+-\d+$"` |

---

## File Structure

```
backend/src/
├── shared/
│   ├── types.py        # NewType ID definitions
│   ├── enums.py        # StrEnum definitions
│   ├── constants.py    # System constants (Final)
│   └── base.py         # Base model configs
└── features/
    ├── users/
    │   └── schemas.py
    ├── sessions/
    │   └── schemas.py
    ├── items/
    │   └── schemas.py
    └── settings/
        └── schemas.py
```

---

## `shared/types.py`

```python
# backend/src/shared/types.py
from typing import NewType
from pydantic import UUID4

# All IDs are UUID version 4.
# NewType provides type-checker distinction between UserId, SessionId, ItemId.
# Pydantic UUID4 validates that the UUID is actually version 4 at parse time.

UserId = NewType("UserId", UUID4)
SessionId = NewType("SessionId", UUID4)
ItemId = NewType("ItemId", UUID4)
```

---

## `shared/enums.py`

```python
# backend/src/shared/enums.py
from enum import StrEnum


class SessionStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"


class ExportStatus(StrEnum):
    NOT_EXPORTED = "not_exported"
    EXPORTED = "exported"
    FAILED = "failed"


class TrackerType(StrEnum):
    YOUTRACK = "youtrack"
    # JIRA = "jira"        # not implemented in MVP
    # LINEAR = "linear"    # not implemented in MVP
    # AZURE_DEVOPS = "azure_devops"  # not implemented in MVP


class UserRole(StrEnum):
    EDITOR = "editor"
    VIEWER = "viewer"


# ERROR CODES — exhaustive list.
# Agent MUST NOT introduce codes outside this enum.
class ErrorCode(StrEnum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    CONFLICT = "CONFLICT"
    CONCURRENT_MODIFICATION = "CONCURRENT_MODIFICATION"
    ITEM_LIMIT_REACHED = "ITEM_LIMIT_REACHED"
    SESSION_APPROVED = "SESSION_APPROVED"
    TRACKER_API_ERROR = "TRACKER_API_ERROR"
    CONNECTION_ERROR = "CONNECTION_ERROR"
    FIELD_MAPPING_ERROR = "FIELD_MAPPING_ERROR"
```

---

## `shared/constants.py`

```python
# backend/src/shared/constants.py
from typing import Final

# PERT formula constants — not configurable in MVP.
# Changes require a code release, not a config change.
CONTINGENCY_FACTOR: Final[float] = 0.1   # hidden_reserve = spread * k
BUFFER_Z_SCORE_95: Final[float] = 1.645  # buffer_95 = sigma_total * z

# Session limits
SESSION_SOFT_CAP: Final[int] = 50   # warning shown to user
SESSION_HARD_CAP: Final[int] = 100  # 409 ITEM_LIMIT_REACHED returned

# JWT TTL
JWT_ACCESS_TTL_MINUTES: Final[int] = 15
JWT_REFRESH_TTL_DAYS: Final[int] = 30

# Focus factor allowed values (Literal enforced in schema)
FOCUS_FACTOR_VALUES: Final[tuple[float, ...]] = (0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
FOCUS_FACTOR_DEFAULT: Final[float] = 0.8

# Session defaults
HOURS_PER_DAY_DEFAULT: Final[int] = 8
```

---

## `shared/base.py`

```python
# backend/src/shared/base.py
from pydantic import BaseModel, ConfigDict


# Canonical config — applied to ALL models in this project.
_BASE_CONFIG = ConfigDict(
    strict=True,            # No implicit type coercion (int "1" ≠ int 1 from JSON string)
    frozen=True,            # Instances are immutable after construction
    populate_by_name=True,  # Allow field name AND alias to populate
    use_enum_values=True,   # Serialize enums as their .value (str), not enum instances
)


class ReadModel(BaseModel):
    """
    Base for all API response schemas.
    Strict + frozen: immutable DTOs returned from backend.
    """
    model_config = _BASE_CONFIG


class WriteModel(BaseModel):
    """
    Base for Create schemas (POST body).
    Strict mode preserved; not frozen (constructed from request data).
    """
    model_config = ConfigDict(
        strict=True,
        frozen=False,
        populate_by_name=True,
        use_enum_values=True,
    )


class UpdateModel(BaseModel):
    """
    Base for Update schemas (PATCH body).
    All fields are Optional — agent MUST NOT make them required.
    Not frozen.
    """
    model_config = ConfigDict(
        strict=True,
        frozen=False,
        populate_by_name=True,
        use_enum_values=True,
    )
```

---

## `features/users/schemas.py`

```python
# backend/src/features/users/schemas.py
from pydantic import EmailStr, Field, field_validator
from pydantic import AwareDatetime

from shared.base import ReadModel, WriteModel
from shared.enums import UserRole
from shared.types import UserId


# ── Annotated field types (reusable) ────────────────────────────────────────

_Email = EmailStr  # validated by email-validator package
_DisplayName = Field(min_length=3, max_length=100)
_RawPassword = Field(min_length=8, max_length=128)


# ── Schemas ──────────────────────────────────────────────────────────────────

class UserCreate(WriteModel):
    """POST /api/auth/register request body."""
    email: _Email
    display_name: str = _DisplayName
    password: str = _RawPassword
    role: UserRole = UserRole.EDITOR

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        # Explicit check kept for clear error message.
        # Field(min_length=8) handles it, but message is generic.
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserRead(ReadModel):
    """API response — never exposes password_hash."""
    id: UserId
    email: str              # str here (already validated on write)
    display_name: str
    role: UserRole
    created_at: AwareDatetime
    last_seen_at: AwareDatetime | None  # None for new users


class UserLogin(WriteModel):
    """POST /api/auth/login request body."""
    email: _Email
    password: str = Field(min_length=1)


class TokenResponse(ReadModel):
    """POST /api/auth/login response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int         # seconds until access_token expiry
```

---

## `features/sessions/schemas.py`

```python
# backend/src/features/sessions/schemas.py
from typing import Annotated, Literal
from pydantic import Field, AwareDatetime

from shared.base import ReadModel, WriteModel, UpdateModel
from shared.enums import SessionStatus
from shared.types import UserId, SessionId
from features.items.schemas import ItemRead


# ── Annotated field types ────────────────────────────────────────────────────

FocusFactor = Literal[0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

HoursPerDay = Annotated[int, Field(gt=0, le=12)]
# gt=0: at least 1 hour per day
# le=12: overtime allowed up to 12h, hard business cap

SessionTitle = Annotated[str, Field(min_length=3, max_length=200)]
SessionDescription = Annotated[str, Field(max_length=2000)]
# description is str (not Optional): empty "" is valid, None is forbidden.


# ── Aggregates (computed on every GET, never stored) ─────────────────────────

class SessionAggregates(ReadModel):
    """
    Session-level PERT aggregates.
    Computed by backend on each GET — not persisted.

    Formulas:
        total_effort   = Σ item.metrics.total_effort
        total_variance = Σ item.metrics.variance
        sigma_total    = sqrt(total_variance)
        buffer_95      = BUFFER_Z_SCORE_95 * sigma_total   # 1.645 * σ
        duration_days  = total_effort / (focus_factor * hours_per_day)

    All values: float, 2 decimal places.
    """
    total_effort: float     # hours
    total_variance: float
    sigma_total: float      # hours
    buffer_95: float        # hours, 95% contingency buffer
    duration_days: float    # calendar days


# ── Session schemas ──────────────────────────────────────────────────────────

class SessionCreate(WriteModel):
    """POST /api/sessions request body."""
    title: SessionTitle
    description: SessionDescription = ""    # default: empty string
    focus_factor: FocusFactor = 0.8
    hours_per_day: HoursPerDay = 8


class SessionUpdate(UpdateModel):
    """
    PATCH /api/sessions/{session_id} request body.
    All fields optional — agent MUST NOT require any.
    Only draft sessions can be updated (enforced in service, not schema).
    """
    title: SessionTitle | None = None
    description: SessionDescription | None = None
    focus_factor: FocusFactor | None = None
    hours_per_day: HoursPerDay | None = None


class SessionRead(ReadModel):
    """
    GET /api/sessions/{session_id} response.
    Includes full items list and aggregates.
    """
    id: SessionId
    user_id: UserId
    title: str
    description: str
    status: SessionStatus
    focus_factor: float             # serialized from Literal via use_enum_values
    hours_per_day: int
    created_at: AwareDatetime
    updated_at: AwareDatetime
    approved_at: AwareDatetime | None
    items: list[ItemRead]           # see items/schemas.py → ItemRead
    aggregates: SessionAggregates


class SessionListItem(ReadModel):
    """
    GET /api/sessions list entry — no items, no aggregates (performance).
    """
    id: SessionId
    user_id: UserId
    title: str
    status: SessionStatus
    focus_factor: float
    hours_per_day: int
    created_at: AwareDatetime
    updated_at: AwareDatetime
    item_count: int                 # computed by backend (COUNT query)


class SessionClone(WriteModel):
    """POST /api/sessions/{session_id}/clone request body."""
    title: SessionTitle
```

---

## `features/items/schemas.py`

```python
# backend/src/features/items/schemas.py
from typing import Annotated
from pydantic import Field, AwareDatetime, model_validator

from shared.base import ReadModel, WriteModel, UpdateModel
from shared.enums import ExportStatus
from shared.types import ItemId, SessionId


# ── Annotated field types ────────────────────────────────────────────────────

EstimationHours = Annotated[int, Field(ge=1, le=999)]
# ge=1: minimum 1 hour (0 is not a valid estimate)
# le=999: maximum ~125 working days at 8h/day

ItemTitle = Annotated[str, Field(min_length=3, max_length=200)]
ItemDescription = Annotated[str, Field(max_length=2000)]
# description: str (not Optional), empty "" allowed, None forbidden

TrackerIssueId = Annotated[
    str,
    Field(pattern=r"^[A-Z0-9]+-\d+$", max_length=100),
]
# Examples: "YT-123", "PROJ-4567", "ABC1-89"
# Tracker-neutral naming (not yt_issue_id).


# ── ItemMetrics — computed fields as composition ─────────────────────────────

class ItemMetrics(ReadModel):
    """
    PERT calculated fields for one EstimationItem.
    Computed by backend service — never accepted from client.

    Formulas (CONTINGENCY_FACTOR = 0.1):
        t_expected     = (optimistic + 4*most_likely + pessimistic) / 6
        spread         = pessimistic - optimistic
        sigma          = spread / 6
        variance       = sigma ** 2
        hidden_reserve = spread * CONTINGENCY_FACTOR
        total_effort   = t_expected + hidden_reserve

    Precision: all values rounded to 2 decimal places before storage and response.

    Numeric example (O=4, M=8, P=12):
        t_expected     = (4 + 32 + 12) / 6 = 8.00
        spread         = 12 - 4            = 8.00
        sigma          = 8 / 6             = 1.33
        variance       = 1.33 ** 2         = 1.78
        hidden_reserve = 8 * 0.1           = 0.80
        total_effort   = 8.00 + 0.80       = 8.80
    """
    t_expected: float       # hours, 2 decimal places
    spread: float           # hours, 2 decimal places
    sigma: float            # hours, 2 decimal places
    variance: float         # float, 2 decimal places
    hidden_reserve: float   # hours, 2 decimal places
    total_effort: float     # hours, 2 decimal places


# ── Item schemas ─────────────────────────────────────────────────────────────

class ItemCreate(WriteModel):
    """
    POST /api/sessions/{session_id}/items request body.

    Constraint: optimistic ≤ most_likely ≤ pessimistic.
    Enforced by @model_validator — NOT by SQL CHECK.
    """
    title: ItemTitle
    description: ItemDescription = ""
    optimistic: EstimationHours
    most_likely: EstimationHours
    pessimistic: EstimationHours

    @model_validator(mode="after")
    def validate_omp_order(self) -> "ItemCreate":
        o, m, p = self.optimistic, self.most_likely, self.pessimistic
        if not (o <= m <= p):
            raise ValueError(
                f"O ≤ M ≤ P violated: optimistic={o}, most_likely={m}, pessimistic={p}"
            )
        return self


class ItemUpdate(UpdateModel):
    """
    PATCH /api/sessions/{session_id}/items/{item_id} request body.
    All fields optional — agent MUST NOT require any.
    O ≤ M ≤ P validated only when 2+ estimation fields are present.
    """
    title: ItemTitle | None = None
    description: ItemDescription | None = None
    optimistic: EstimationHours | None = None
    most_likely: EstimationHours | None = None
    pessimistic: EstimationHours | None = None

    @model_validator(mode="after")
    def validate_omp_if_present(self) -> "ItemUpdate":
        o = self.optimistic
        m = self.most_likely
        p = self.pessimistic
        # Validate only when all three are provided in this update.
        if o is not None and m is not None and p is not None:
            if not (o <= m <= p):
                raise ValueError(
                    f"O ≤ M ≤ P violated: optimistic={o}, most_likely={m}, pessimistic={p}"
                )
        return self


class ItemRead(ReadModel):
    """
    API response for a single EstimationItem.
    Canonical schema — used by both items-api and sessions-api (items list).
    metrics field contains all computed PERT values.
    """
    id: ItemId
    session_id: SessionId
    title: str
    description: str                    # never None in response
    optimistic: int
    most_likely: int
    pessimistic: int
    metrics: ItemMetrics                # nested — see ItemMetrics above
    tracker_issue_id: TrackerIssueId | None
    export_status: ExportStatus
    created_at: AwareDatetime
    updated_at: AwareDatetime


class ItemBatchUpdateEntry(UpdateModel):
    """Single entry in PATCH /api/sessions/{id}/items/batch."""
    id: ItemId                          # required: identifies which item to update
    title: ItemTitle | None = None
    description: ItemDescription | None = None
    optimistic: EstimationHours | None = None
    most_likely: EstimationHours | None = None
    pessimistic: EstimationHours | None = None

    @model_validator(mode="after")
    def validate_omp_if_present(self) -> "ItemBatchUpdateEntry":
        o, m, p = self.optimistic, self.most_likely, self.pessimistic
        if o is not None and m is not None and p is not None:
            if not (o <= m <= p):
                raise ValueError(
                    f"O ≤ M ≤ P violated: optimistic={o}, most_likely={m}, pessimistic={p}"
                )
        return self


class ItemBatchUpdate(WriteModel):
    """PATCH /api/sessions/{session_id}/items/batch request body."""
    items: list[ItemBatchUpdateEntry] = Field(min_length=1)
```

---

## `features/settings/schemas.py`

```python
# backend/src/features/settings/schemas.py
from pydantic import Field, AwareDatetime, field_validator

from shared.base import ReadModel, WriteModel
from shared.enums import TrackerType


# ── Annotated field types ────────────────────────────────────────────────────

TrackerToken = Field(min_length=10, max_length=512)
# min_length=10: basic sanity check, not format-specific
# Token is never returned in responses (write-only)

TrackerUrl = Field(
    pattern=r"^https?://[^\s/$.?#].[^\s]*$",
    max_length=500,
)


# ── Settings schemas ─────────────────────────────────────────────────────────

class TrackerConfigureRequest(WriteModel):
    """
    POST /api/settings/tracker request body.
    Token is encrypted before storage — never returned in responses.
    """
    tracker_type: TrackerType
    base_url: str = TrackerUrl
    token: str = TrackerToken

    @field_validator("tracker_type")
    @classmethod
    def only_youtrack_in_mvp(cls, v: str) -> str:
        if v != TrackerType.YOUTRACK:
            raise ValueError(
                f"Only 'youtrack' is supported in MVP. Got: {v!r}"
            )
        return v


class TrackerTestRequest(WriteModel):
    """POST /api/settings/tracker/test — test without saving."""
    tracker_type: TrackerType
    base_url: str = TrackerUrl
    token: str = TrackerToken


class TrackerStatusRead(ReadModel):
    """
    GET /api/settings/tracker response.
    Token is NEVER included — write-only field.
    """
    tracker_type: TrackerType | None
    base_url: str | None
    is_active: bool
    last_verified_at: AwareDatetime | None
    configured: bool        # True when tracker_type and base_url are set


class ProjectRead(ReadModel):
    """Single tracker project."""
    id: str
    name: str
    short_name: str


class ProjectFieldRead(ReadModel):
    """Single field descriptor from tracker project."""
    name: str
    type: str               # "string" | "text" | "number" — tracker-native type names
    required: bool


class ProjectWithFieldsRead(ReadModel):
    """GET /api/settings/tracker/projects response item."""
    id: str
    name: str
    short_name: str
    fields: list[ProjectFieldRead]


# ── Field mapping ─────────────────────────────────────────────────────────────

class ItemFieldName(str):
    """
    Valid item_field values for ProjectFieldMap.
    Exhaustive — agent MUST NOT add values outside this set.
    """
    # Used as: Literal["title", "description", "total_effort"]

from typing import Literal

MappableItemField = Literal["title", "description", "total_effort"]


class FieldMappingEntry(WriteModel):
    """Single field mapping rule."""
    item_field: MappableItemField
    tracker_field: str = Field(min_length=1, max_length=200)


class ProjectMappingRequest(WriteModel):
    """POST /api/settings/tracker/projects/{project_id}/mapping."""
    mappings: list[FieldMappingEntry] = Field(min_length=1)


class ProjectMappingRead(ReadModel):
    """GET /api/settings/tracker/projects/{project_id}/mapping."""
    project_id: str
    mappings: list[FieldMappingEntry]
```

---

## `shared/errors.py`

```python
# backend/src/shared/errors.py
from pydantic import Field
from shared.base import ReadModel
from shared.enums import ErrorCode


class ErrorResponse(ReadModel):
    """
    Canonical error response for ALL endpoints.
    No other error shape is valid.

    HTTP status is set in the response header — not in this body.
    """
    code: ErrorCode
    message: str = Field(min_length=1, max_length=500)
    detail: str = Field(default="", max_length=2000)
    request_id: str = Field(default="", max_length=100)


class ConflictDetail(ReadModel):
    """
    Body extension for CONCURRENT_MODIFICATION (409).
    Included as detail payload alongside ErrorResponse.
    """
    expected_updated_at: str    # AwareDatetime ISO string client sent
    actual_updated_at: str      # AwareDatetime ISO string from DB
```

---

## Invariants Reference (for agents)

```
RULE 1: O ≤ M ≤ P
  Enforced: ItemCreate @model_validator, ItemUpdate @model_validator
  NOT enforced: SQL CHECK constraint (by design — Q4)

RULE 2: Session immutability after approval
  Enforced: service layer
  Schema signal: SessionUpdate has no 'status' field (cannot be set via PATCH)
  Approval: POST /api/sessions/{id}/approve (dedicated endpoint)

RULE 3: TrackerConnection — one active at a time
  Enforced: partial unique index on DB level
  Schema: no field for this constraint (DB invariant only)

RULE 4: tracker_issue_id uniqueness per session
  Enforced: service layer (idempotency check before export)
  Schema: TrackerIssueId type validates format

RULE 5: ItemMetrics computed by backend only
  ItemRead.metrics is ALWAYS populated by backend
  Client MUST NOT send metrics in any write request
  ItemCreate and ItemUpdate have NO metrics field — by design

RULE 6: description is str, never None
  Default: "" (empty string)
  API response: always str
  DB: NOT NULL DEFAULT ''

RULE 7: focus_factor is Literal[0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
  Only these 6 values accepted in strict mode
  Default: 0.8

RULE 8: ErrorCode is exhaustive
  Agent MUST use ErrorCode enum only
  New codes require a code release + enum update
```

---

## SQLAlchemy Column Types (mapping)

```python
# Mapping from Pydantic schema → SQLAlchemy column type

# IDs
id: UserId        → Column(Uuid, primary_key=True, default=uuid4)
id: SessionId     → Column(Uuid, primary_key=True, default=uuid4)
id: ItemId        → Column(Uuid, primary_key=True, default=uuid4)

# Enums (stored as VARCHAR, not DB ENUM — portable across SQLite/PG)
status: SessionStatus    → Column(String(20), nullable=False)
role: UserRole           → Column(String(20), nullable=False)
export_status: ExportStatus → Column(String(20), nullable=False, default="not_exported")
tracker_type: TrackerType   → Column(String(30), nullable=False)

# Estimation hours
optimistic: int   → Column(SmallInteger, nullable=False)   # max 999 fits SmallInteger
most_likely: int  → Column(SmallInteger, nullable=False)
pessimistic: int  → Column(SmallInteger, nullable=False)

# Calculated fields
t_expected: float → Column(Numeric(7, 2), nullable=False)  # max 999.99
sigma: float      → Column(Numeric(7, 2), nullable=False)
variance: float   → Column(Numeric(9, 2), nullable=False)  # sigma^2 can be larger
hidden_reserve: float → Column(Numeric(7, 2), nullable=False)
total_effort: float   → Column(Numeric(7, 2), nullable=False)

# Focus factor
focus_factor: float → Column(Numeric(3, 2), nullable=False, default=0.8)

# Timestamps
created_at: AwareDatetime → Column(DateTime(timezone=True), nullable=False,
                                   server_default=func.now())
updated_at: AwareDatetime → Column(DateTime(timezone=True), nullable=False,
                                   onupdate=func.now())
approved_at: AwareDatetime | None → Column(DateTime(timezone=True), nullable=True)

# description
description: str  → Column(Text, nullable=False, default="")

# tracker_issue_id
tracker_issue_id: str | None → Column(String(100), nullable=True)
```

---

## DB Indexes

```sql
-- Users
CREATE UNIQUE INDEX idx_users_email ON users(email);

-- Sessions
CREATE INDEX idx_sessions_user_id ON estimation_sessions(user_id);
CREATE INDEX idx_sessions_status ON estimation_sessions(status);

-- Items
CREATE INDEX idx_items_session_id ON estimation_items(session_id);
CREATE INDEX idx_items_tracker_issue_id ON estimation_items(tracker_issue_id)
    WHERE tracker_issue_id IS NOT NULL;

-- TrackerConnection: only one active record allowed
CREATE UNIQUE INDEX idx_tracker_connection_active
    ON tracker_connections(is_active)
    WHERE is_active = true;

-- ProjectFieldMap: unique combination
CREATE UNIQUE INDEX idx_project_field_map_unique
    ON project_field_maps(tracker_project_id, item_field);
```

---

## Migration Order

```
001_create_users.py
002_create_tracker_connections.py
003_create_estimation_sessions.py      ← FK → users
004_create_estimation_items.py         ← FK → estimation_sessions
005_create_project_field_maps.py
```

**Dependency order**: User → TrackerConnection → EstimationSession → EstimationItem → ProjectFieldMap