from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from ...core.db import Base
from ...shared.enums import SessionStatus
from ...shared.types import SessionId, UserId


class Session(Base):
    """Estimation session model.

    Represents a PERT estimation session with work items. A session belongs to
    a user and can contain multiple EstimationItem instances.
    """

    __tablename__ = "estimation_sessions"

    id: Mapped[SessionId] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[UserId] = mapped_column(nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
        default="",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=SessionStatus.DRAFT,
    )
    focus_factor: Mapped[float] = mapped_column(nullable=False)
    hours_per_day: Mapped[int] = mapped_column(nullable=False)
    contingency_factor: Mapped[float] = mapped_column(
        nullable=False,
        default=0.1,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships — items relationship will be fully configured in T026
    # when EstimationItem model is created. For now, no relationship defined
    # to avoid circular dependency with non-existent model.

    __table_args__ = (
        CheckConstraint(
            "focus_factor IN (0.5, 0.6, 0.7, 0.8, 0.9, 1.0)",
            name="ck_valid_focus_factor",
        ),
        CheckConstraint(
            "contingency_factor IN (0.05, 0.1, 0.15, 0.2)",
            name="ck_valid_contingency_factor",
        ),
        CheckConstraint("hours_per_day > 0", name="ck_positive_hours"),
    )
