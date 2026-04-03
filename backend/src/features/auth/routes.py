from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import Settings, get_settings
from ...core.db import get_db
from ...core.security import get_current_user_email
from ...shared.enums import UserRole
from ...shared.types import UserId
from .schemas import RefreshRequest, TokenResponse, UserCreate, UserLogin, UserRead
from .services import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _make_token_response(svc_response: object) -> TokenResponse:
    """Convert AuthService.TokenResponse → schema TokenResponse."""
    from .services import TokenResponse as SvcToken  # noqa: PLC0415

    assert isinstance(svc_response, SvcToken)
    return TokenResponse(
        access_token=svc_response.access_token,
        refresh_token=svc_response.refresh_token,
        token_type=svc_response.token_type,
        expires_in=svc_response.expires_in,
    )


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    body: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    svc = AuthService(db, settings)
    result = await svc.register(
        email=str(body.email),
        display_name=body.display_name,
        password=body.password,
        role=body.role,
    )
    return _make_token_response(result)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and receive JWT tokens",
)
async def login(
    body: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    svc = AuthService(db, settings)
    result = await svc.login(email=str(body.email), password=body.password)
    return _make_token_response(result)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Exchange refresh token for a new token pair",
)
async def refresh(
    body: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    svc = AuthService(db, settings)
    result = await svc.refresh(refresh_token=body.refresh_token)
    return _make_token_response(result)


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get current authenticated user",
)
async def get_me(
    email: Annotated[str, Depends(get_current_user_email)],
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UserRead:
    svc = AuthService(db, settings)
    user = await svc.get_current_user(email=email)
    return UserRead(
        id=UserId(user.id),
        email=user.email,
        display_name=user.display_name,
        role=UserRole(user.role),
        created_at=user.created_at,
        last_seen_at=user.last_seen_at,
    )
