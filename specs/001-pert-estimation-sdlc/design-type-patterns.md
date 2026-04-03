# Appendix: Canonical Type Patterns

**Status**: Mandatory reference — agents MUST use these patterns verbatim.
**Rule**: If your code does not match one of these patterns, STOP and re-read this file.
A file with missing type annotations is considered UNWRITTEN regardless of logic correctness.

---

## 0. File Header (every Python file)

```python
from __future__ import annotations
```

First line of every Python file. Enables postponed evaluation of annotations —
required for forward references in SQLAlchemy models and circular type hints.

---

## 1. SQLAlchemy Models

```python
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, Float, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base
from src.shared.types import SessionId, UserId


class EstimationSession(Base):
    __tablename__ = "estimation_sessions"
    __table_args__ = (
        CheckConstraint("status IN ('draft', 'approved')", name="ck_sessions_status"),
        CheckConstraint("ff > 0", name="ck_sessions_ff_positive"),
        CheckConstraint(
            "hours_per_day BETWEEN 1 AND 10",
            name="ck_sessions_hours_range",
        ),
    )

    id: Mapped[SessionId] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    k: Mapped[float] = mapped_column(Float, nullable=False, default=0.1)
    ff: Mapped[float] = mapped_column(Float, nullable=False, default=0.8)
    hours_per_day: Mapped[int] = mapped_column(Integer, nullable=False, default=8)
    risk_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=5.0)
    public_token: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    creator_id: Mapped[UserId] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )
```

**Rules:**
- Every column: `Mapped[T]` — never bare `Column()`
- Nullable columns: `Mapped[T | None]`
- All constraints in `__table_args__`
- `from __future__ import annotations` always first

---

## 2. Pydantic Schemas (Commands & Responses)

```python
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from src.shared.types import SessionId, UserId


# ── Commands (input) ──────────────────────────────────────────────────────────

class CreateSessionCommand(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=200, description="Session name")]
    k: Annotated[float, Field(default=0.1, ge=0.0, le=1.0, description="Hidden work coefficient")]
    ff: Annotated[float, Field(default=0.8, gt=0.0, le=1.0, description="Focus Factor")]
    hours_per_day: Annotated[int, Field(default=8, ge=1, le=10, description="Working hours per day")]
    risk_threshold: Annotated[float, Field(default=5.0, gt=0.0, description="Spread threshold for risk highlight")]
    yt_project_id: Annotated[str | None, Field(default=None)]


# ── Responses (output) ────────────────────────────────────────────────────────

class SessionResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: SessionId
    name: str
    status: str
    export_status: str
    k: float
    ff: float
    hours_per_day: int
    risk_threshold: float
    creator_id: UserId
    created_at: datetime
    updated_at: datetime
```

**Rules:**
- Commands: input validation via `Annotated[T, Field(...)]`
- Responses: `model_config = {"from_attributes": True}` always present
- Never use `Optional[T]` — use `T | None` (Python 3.10+ union syntax)
- Never use bare `str` for IDs — use `SessionId`, `ItemId`, `UserId`

---

## 3. FastAPI Routes

```python
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_db
from src.core.security import require_editor
from src.features.sessions.commands import CreateSessionCommand
from src.features.sessions.schemas import SessionResponse
from src.features.sessions.services import SessionService
from src.models.user import User

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new estimation session",
)
async def create_session(
    cmd: CreateSessionCommand,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_editor)],
) -> SessionResponse:
    service = SessionService(db)
    return await service.create(cmd, creator_id=current_user.id)


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    summary="Get session by ID",
)
async def get_session(
    session_id: SessionId,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_any)],
) -> SessionResponse:
    service = SessionService(db)
    result = await service.get_by_id(session_id)
    if result is None:
        raise NotFoundError("session", session_id)
    return result
```

**Rules:**
- Every route: explicit `response_model=` and `status_code=`
- Every parameter: `Annotated[T, Depends(...)]` — never bare `= Depends(...)`
- Return type annotation always matches `response_model`
- Never `-> dict` or `-> Any`

---

## 4. Service Methods

```python
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.sessions.commands import CreateSessionCommand
from src.features.sessions.models import EstimationSession
from src.features.sessions.schemas import SessionResponse
from src.shared.types import SessionId, UserId


class SessionService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(
        self,
        cmd: CreateSessionCommand,
        creator_id: UserId,
    ) -> SessionResponse:
        session = EstimationSession(
            name=cmd.name,
            k=cmd.k,
            ff=cmd.ff,
            hours_per_day=cmd.hours_per_day,
            risk_threshold=cmd.risk_threshold,
            creator_id=creator_id,
        )
        self._db.add(session)
        await self._db.commit()
        await self._db.refresh(session)
        return SessionResponse.model_validate(session)

    async def get_by_id(
        self,
        session_id: SessionId,
    ) -> SessionResponse | None:
        stmt = select(EstimationSession).where(EstimationSession.id == session_id)
        result = await self._db.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return SessionResponse.model_validate(row)
```

**Rules:**
- `__init__` always annotated: `self._db: AsyncSession`
- `__init__` always returns `-> None`
- Every method: explicit return type, including `-> None` for void methods
- Class-level attributes declared before `__init__` if needed by mypy

---

## 5. Command Classes

```python
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Annotated

from src.shared.types import SessionId, UserId


class ApproveSessionCommand(BaseModel):
    session_id: SessionId
    approved_by: UserId


class CloneSessionCommand(BaseModel):
    source_session_id: SessionId
    new_name: Annotated[str, Field(min_length=1, max_length=200)]
    cloned_by: UserId
```

**Rules:**
- Commands are `BaseModel`, never dataclasses or plain dicts
- All fields annotated — no bare `str`, `int`, `float` without `Annotated` where constraints exist
- Commands are immutable input contracts — no methods, no logic

---

## 6. Port Protocols

```python
from __future__ import annotations

from typing import Protocol

from src.features.export.schemas import (
    ConnectionResult,
    CreatedIssue,
    Field,
    IssuePayload,
    Project,
)


class IssueTrackerPort(Protocol):
    async def test_connection(self) -> ConnectionResult: ...
    async def list_projects(self) -> list[Project]: ...
    async def get_project_fields(self, project_id: str) -> list[Field]: ...
    async def create_issue(
        self,
        project_id: str,
        payload: IssuePayload,
    ) -> CreatedIssue: ...
```

**Rules:**
- Protocol methods: always annotated, body is `...`
- Never `-> Any` in Protocol definitions
- Import all referenced types explicitly — no `TYPE_CHECKING` tricks

---

## 7. Error Handling

```python
from __future__ import annotations

import uuid

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from src.shared.models.error import ErrorResponse


class NotFoundError(HTTPException):
    def __init__(self, resource: str, resource_id: object) -> None:
        super().__init__(
            status_code=404,
            detail=ErrorResponse(
                code="NOT_FOUND",
                message=f"{resource} not found",
                detail=f"id={resource_id}",
                request_id=str(uuid.uuid4()),
            ).model_dump(),
        )


class ConflictError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(
            status_code=409,
            detail=ErrorResponse(
                code="CONFLICT",
                message=message,
                detail=None,
                request_id=str(uuid.uuid4()),
            ).model_dump(),
        )
```

**Rules:**
- Never `raise HTTPException(detail="raw string")` — PROHIBITED
- Always wrap in typed exception class that produces `ErrorResponse`
- `request_id` always present — use `uuid.uuid4()`

---

## 8. PERT Calculation Service

```python
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class PertMetrics:
    t_expected: float
    spread: float
    sigma: float
    variance: float
    hidden_reserve: float
    total_effort: float
    duration_days: float


def calculate_pert(
    optimistic: float,
    most_likely: float,
    pessimistic: float,
    k: float,
    ff: float,
    hours_per_day: int,
) -> PertMetrics:
    """Calculate all PERT metrics for a single item.

    Canonical formulas (Constitution design.md):
        t_expected      = (O + 4M + P) / 6
        spread          = P - O
        sigma           = spread / 6
        variance        = sigma ** 2
        hidden_reserve  = spread * k
        total_effort    = t_expected + hidden_reserve
        duration_days   = total_effort / (ff * hours_per_day)
    """
    t_expected = (optimistic + 4 * most_likely + pessimistic) / 6
    spread = pessimistic - optimistic
    sigma = spread / 6
    variance = sigma**2
    hidden_reserve = spread * k
    total_effort = t_expected + hidden_reserve
    duration_days = total_effort / (ff * hours_per_day)

    return PertMetrics(
        t_expected=round(t_expected, 3),
        spread=round(spread, 3),
        sigma=round(sigma, 3),
        variance=round(variance, 3),
        hidden_reserve=round(hidden_reserve, 3),
        total_effort=round(total_effort, 3),
        duration_days=round(duration_days, 3),
    )
```

**Rules:**
- `PertMetrics` is a frozen dataclass — immutable, all fields typed
- No `Any` in inputs or outputs
- Docstring includes formula reference to design.md

---

## 9. Shared Types

```python
# src/shared/types.py
from __future__ import annotations

import uuid
from typing import NewType

# All IDs are NewType — prevents mixing SessionId with ItemId at type-check level
UserId = NewType("UserId", uuid.UUID)
SessionId = NewType("SessionId", uuid.UUID)
ItemId = NewType("ItemId", uuid.UUID)
```

**Rules:**
- This file is the ONLY place where NewType IDs are defined
- Never define local ID types in feature modules
- Always import from `src.shared.types`

---

## 10. mypy Configuration Reference

```toml
# pyproject.toml — mandatory mypy section
[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["pydantic.mypy"]

[[tool.mypy.overrides]]
module = ["sqlalchemy.*", "alembic.*"]
ignore_missing_imports = true
```

**What `strict = true` enforces (agent must know):**
- `disallow_untyped_defs = true` → every function needs annotations
- `disallow_any_generics = true` → `list` forbidden, must be `list[str]`
- `warn_return_any = true` → `-> Any` is an error
- `no_implicit_optional = true` → `x: str = None` is an error, must be `x: str | None = None`
- `disallow_untyped_calls = true` → cannot call untyped functions

---

## File Completion Checklist

**A Python file is considered COMPLETE only when ALL of the following pass:**

```
□ from __future__ import annotations  ← first line
□ Every function has parameter type annotations
□ Every function has return type annotation (including -> None)
□ No bare list, dict, tuple — always list[T], dict[K, V], tuple[T, ...]
□ No Optional[T] — use T | None
□ No Any without an explicit # type: ignore[...] comment with justification
□ just be-check-file src/features/{feature}/{file}.py → exit code 0
□ git commit
```

**Do NOT move to the next file until exit code is 0.**