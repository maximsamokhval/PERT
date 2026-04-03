from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.sessions.models import Session
from src.shared.enums import SessionStatus


class TestSessionModel:
    """Tests for the Session SQLAlchemy model (T025)."""

    @pytest.mark.asyncio
    async def test_session_creation_with_defaults(self, db_session: AsyncSession) -> None:
        """Test that a Session can be created with default values."""
        user_id = uuid.uuid4()
        session = Session(
            user_id=user_id,  # type: ignore[arg-type]
            title="Test Session",
            description="Test description",
            focus_factor=0.8,
            hours_per_day=8,
        )

        db_session.add(session)
        await db_session.flush()

        # Verify defaults
        assert session.status == SessionStatus.DRAFT
        assert session.description == "Test description"
        assert session.contingency_factor == 0.1
        assert session.approved_at is None
        assert session.created_at is not None
        assert session.updated_at is not None

    @pytest.mark.asyncio
    async def test_session_retrieval(self, db_session: AsyncSession) -> None:
        """Test that a Session can be retrieved by ID."""
        user_id = uuid.uuid4()
        session = Session(
            user_id=user_id,  # type: ignore[arg-type]
            title="Retrieval Test",
            focus_factor=0.8,
            hours_per_day=8,
        )

        db_session.add(session)
        await db_session.flush()
        session_id = session.id

        result = await db_session.execute(select(Session).where(Session.id == session_id))
        retrieved = result.scalar_one()

        assert retrieved.title == "Retrieval Test"
        assert retrieved.focus_factor == 0.8

    @pytest.mark.asyncio
    async def test_session_status_update_to_approved(self, db_session: AsyncSession) -> None:
        """Test that session status can be updated to approved with approved_at timestamp."""
        user_id = uuid.uuid4()
        session = Session(
            user_id=user_id,  # type: ignore[arg-type]
            title="Approval Test",
            focus_factor=0.8,
            hours_per_day=8,
        )

        db_session.add(session)
        await db_session.flush()

        # Simulate approval
        session.status = SessionStatus.APPROVED
        session.approved_at = datetime.now(UTC)
        await db_session.flush()

        assert session.status == SessionStatus.APPROVED
        assert session.approved_at is not None

    @pytest.mark.asyncio
    async def test_session_with_all_focus_factors(self, db_session: AsyncSession) -> None:
        """Test that all valid focus_factor values are accepted."""
        valid_factors = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

        for factor in valid_factors:
            user_id = uuid.uuid4()
            session = Session(
                user_id=user_id,  # type: ignore[arg-type]
                title=f"FF={factor}",
                focus_factor=factor,
                hours_per_day=8,
            )
            db_session.add(session)
            await db_session.flush()
            assert session.focus_factor == factor

    @pytest.mark.asyncio
    async def test_session_with_all_contingency_factors(self, db_session: AsyncSession) -> None:
        """Test that all valid contingency_factor values are accepted."""
        valid_factors = [0.05, 0.1, 0.15, 0.2]

        for factor in valid_factors:
            user_id = uuid.uuid4()
            session = Session(
                user_id=user_id,  # type: ignore[arg-type]
                title=f"CF={factor}",
                focus_factor=0.8,
                hours_per_day=8,
                contingency_factor=factor,
            )
            db_session.add(session)
            await db_session.flush()
            assert session.contingency_factor == factor
