from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import Settings
from ...core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from ...shared.enums import UserRole
from ...shared.types import UserId
from .models import User


class TokenResponse:
    """Auth token response — plain slots class, not Pydantic, to avoid circular schema deps."""

    __slots__ = ("access_token", "refresh_token", "token_type", "expires_in")

    def __init__(
        self,
        access_token: str,
        refresh_token: str,
        expires_in: int,
    ) -> None:
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_type = "bearer"
        self.expires_in = expires_in


class AuthService:
    """Authentication service: register, login, token refresh.

    Receives an AsyncSession and Settings via constructor — no module-level
    calls per Constitution Principle VI.
    """

    def __init__(self, db: AsyncSession, settings: Settings) -> None:
        self._db = db
        self._settings = settings

    # ── Internal helpers ────────────────────────────────────────────────────

    async def _get_user_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_user_by_id(self, user_id: UserId) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    def _build_token_response(self, email: str) -> TokenResponse:
        access_token = create_access_token(email, self._settings)
        refresh_token = create_refresh_token(email, self._settings)
        expires_in = self._settings.access_token_expire_minutes * 60
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        )

    # ── Public API ──────────────────────────────────────────────────────────

    async def register(
        self,
        *,
        email: str,
        display_name: str,
        password: str,
        role: UserRole = UserRole.EDITOR,
    ) -> TokenResponse:
        """Create a new user account.

        Raises 409 CONFLICT if the email is already registered.
        Returns a token pair on success.
        """
        existing = await self._get_user_by_email(email)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email already registered: {email}",
            )

        user = User(
            id=UserId(uuid.uuid4()),
            email=email,
            display_name=display_name,
            password_hash=hash_password(password),
            role=role.value,
        )
        self._db.add(user)
        await self._db.commit()
        await self._db.refresh(user)

        return self._build_token_response(email)

    async def login(self, *, email: str, password: str) -> TokenResponse:
        """Authenticate a user by email and password.

        Returns 401 for both non-existent users and wrong passwords to prevent
        email enumeration.
        """
        user = await self._get_user_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Update last_seen_at
        user.last_seen_at = datetime.now(UTC)
        await self._db.commit()

        return self._build_token_response(email)

    async def refresh(self, *, refresh_token: str) -> TokenResponse:
        """Exchange a valid refresh token for a new token pair.

        Raises 401 if the refresh token is invalid or expired.
        """
        email = decode_refresh_token(refresh_token, self._settings)
        user = await self._get_user_by_email(email)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        return self._build_token_response(email)

    async def get_current_user(self, *, email: str) -> User:
        """Load the User record for the authenticated email.

        Raises 401 if the user no longer exists in the database.
        """
        user = await self._get_user_by_email(email)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        return user
