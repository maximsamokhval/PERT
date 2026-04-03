from __future__ import annotations

from pydantic import AwareDatetime, EmailStr, Field

from ...shared.base import ReadModel, WriteModel
from ...shared.enums import UserRole
from ...shared.types import UserId


class UserCreate(WriteModel):
    """POST /api/auth/register request body."""

    email: EmailStr
    display_name: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.EDITOR


class UserLogin(WriteModel):
    """POST /api/auth/login request body."""

    email: EmailStr
    password: str = Field(min_length=1)


class RefreshRequest(WriteModel):
    """POST /api/auth/refresh request body."""

    refresh_token: str = Field(min_length=1)


class TokenResponse(ReadModel):
    """Token pair returned on login, register, and refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until access_token expiry


class UserRead(ReadModel):
    """GET /api/auth/me response — never exposes password_hash."""

    id: UserId
    email: str
    display_name: str
    role: UserRole
    created_at: AwareDatetime
    last_seen_at: AwareDatetime | None
