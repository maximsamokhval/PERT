"""
TDD RED phase — auth service unit tests.

These tests define the expected behaviour of AuthService BEFORE implementation.
Run `just be-test-file tests/unit/test_auth_service.py` to confirm RED (failures).
Implement AuthService, then re-run to confirm GREEN.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.security import hash_password
from src.shared.enums import UserRole

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_settings() -> MagicMock:
    settings = MagicMock()
    settings.jwt_secret_key = "test-secret-key-long-enough"
    settings.jwt_algorithm = "HS256"
    settings.access_token_expire_minutes = 15
    settings.refresh_token_expire_days = 30
    return settings


# ---------------------------------------------------------------------------
# Registration tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_register_creates_user_with_hashed_password(
    mock_db: AsyncMock,
    mock_settings: MagicMock,
) -> None:
    """Registering a user stores a bcrypt hash, never the plain password."""
    from src.features.auth.services import AuthService

    service = AuthService(mock_db, mock_settings)

    mock_db.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
    )
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    with patch("src.features.auth.services.AuthService._get_user_by_email", return_value=None):
        await service.register(
            email="test@example.com",
            display_name="Test User",
            password="secret1234",
            role=UserRole.EDITOR,
        )

    # add() must be called — a user was created
    mock_db.add.assert_called_once()
    user_arg = mock_db.add.call_args[0][0]
    assert user_arg.email == "test@example.com"
    assert user_arg.display_name == "Test User"
    # password must NOT be stored in plain text
    assert user_arg.password_hash != "secret1234"
    # it must be a valid bcrypt hash
    assert user_arg.password_hash.startswith("$2b$")


@pytest.mark.asyncio
async def test_register_raises_conflict_for_duplicate_email(
    mock_db: AsyncMock,
    mock_settings: MagicMock,
) -> None:
    """Registering with an existing email raises a 409 Conflict."""
    from fastapi import HTTPException

    from src.features.auth.models import User
    from src.features.auth.services import AuthService

    service = AuthService(mock_db, mock_settings)
    existing_user = MagicMock(spec=User)
    existing_user.email = "taken@example.com"

    _patch = "src.features.auth.services.AuthService._get_user_by_email"
    with (
        patch(_patch, return_value=existing_user),
        pytest.raises(HTTPException) as exc_info,
    ):
        await service.register(
            email="taken@example.com",
            display_name="New User",
            password="secret1234",
            role=UserRole.EDITOR,
        )

    assert exc_info.value.status_code == 409


# ---------------------------------------------------------------------------
# Login tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_login_returns_tokens_for_valid_credentials(
    mock_db: AsyncMock,
    mock_settings: MagicMock,
) -> None:
    """Successful login returns access_token and refresh_token strings."""
    from src.features.auth.models import User
    from src.features.auth.services import AuthService

    service = AuthService(mock_db, mock_settings)
    user = MagicMock(spec=User)
    user.email = "user@example.com"
    user.password_hash = hash_password("correct-password")
    user.role = UserRole.EDITOR

    mock_db.execute = AsyncMock()
    mock_db.commit = AsyncMock()

    with patch("src.features.auth.services.AuthService._get_user_by_email", return_value=user):
        result = await service.login(email="user@example.com", password="correct-password")

    assert result.access_token
    assert result.refresh_token
    assert result.token_type == "bearer"
    assert result.expires_in > 0


@pytest.mark.asyncio
async def test_login_raises_401_for_wrong_password(
    mock_db: AsyncMock,
    mock_settings: MagicMock,
) -> None:
    """Login with wrong password raises 401 Unauthorized."""
    from fastapi import HTTPException

    from src.features.auth.models import User
    from src.features.auth.services import AuthService

    service = AuthService(mock_db, mock_settings)
    user = MagicMock(spec=User)
    user.email = "user@example.com"
    user.password_hash = hash_password("correct-password")

    _patch = "src.features.auth.services.AuthService._get_user_by_email"
    with patch(_patch, return_value=user), pytest.raises(HTTPException) as exc_info:
        await service.login(email="user@example.com", password="wrong-password")

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_login_raises_401_for_nonexistent_user(
    mock_db: AsyncMock,
    mock_settings: MagicMock,
) -> None:
    """Login for non-existent user raises 401 (not 404) to prevent email enumeration."""
    from fastapi import HTTPException

    from src.features.auth.services import AuthService

    service = AuthService(mock_db, mock_settings)

    _patch = "src.features.auth.services.AuthService._get_user_by_email"
    with patch(_patch, return_value=None), pytest.raises(HTTPException) as exc_info:
        await service.login(email="nobody@example.com", password="any-password")

    assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# Token refresh tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_refresh_returns_new_access_token(
    mock_db: AsyncMock,
    mock_settings: MagicMock,
) -> None:
    """A valid refresh token produces a new access token."""
    from src.core.security import create_refresh_token
    from src.features.auth.models import User
    from src.features.auth.services import AuthService

    service = AuthService(mock_db, mock_settings)
    user = MagicMock(spec=User)
    user.email = "user@example.com"
    user.role = UserRole.EDITOR

    refresh_token = create_refresh_token("user@example.com", mock_settings)

    with patch("src.features.auth.services.AuthService._get_user_by_email", return_value=user):
        result = await service.refresh(refresh_token=refresh_token)

    assert result.access_token
    assert result.refresh_token
    assert result.token_type == "bearer"


@pytest.mark.asyncio
async def test_refresh_raises_401_for_invalid_token(
    mock_db: AsyncMock,
    mock_settings: MagicMock,
) -> None:
    """An invalid or expired refresh token raises 401."""
    from fastapi import HTTPException

    from src.features.auth.services import AuthService

    service = AuthService(mock_db, mock_settings)

    with pytest.raises(HTTPException) as exc_info:
        await service.refresh(refresh_token="not.a.valid.token")

    assert exc_info.value.status_code == 401
