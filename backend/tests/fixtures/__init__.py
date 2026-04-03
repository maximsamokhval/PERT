"""
Shared pytest fixtures for backend tests.

Usage: import fixtures in conftest.py or directly in test files:
    from tests.fixtures import async_client, db_session, auth_token, editor_user
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import Settings
from src.core.db import Base, get_db
from src.core.security import create_access_token, hash_password
from src.features.auth.models import User
from src.shared.enums import UserRole
from src.shared.types import UserId

# ── Test database (in-memory SQLite) ──────────────────────────────────────────

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    return Settings(
        database_url=TEST_DATABASE_URL,
        jwt_secret_key="test-secret-key-at-least-32-chars-long",
        jwt_algorithm="HS256",
        access_token_expire_minutes=15,
        refresh_token_expire_days=30,
        encryption_key="test-fernet-key-placeholder",
        debug=False,
    )


@pytest_asyncio.fixture(scope="function")
async def db_session(test_settings: Settings) -> AsyncGenerator[AsyncSession, None]:
    """Yield an AsyncSession backed by an in-memory SQLite database.

    Schema is created fresh for each test function and torn down afterwards.
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_client(
    db_session: AsyncSession,
    test_settings: Settings,
) -> AsyncGenerator[AsyncClient, None]:
    """Yield an httpx.AsyncClient wired to the FastAPI app with overridden DB and settings."""
    from src.core.config import get_settings  # noqa: PLC0415
    from src.main import app  # noqa: PLC0415

    async def _override_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_settings] = lambda: test_settings

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()


# ── Auth helpers ───────────────────────────────────────────────────────────────


@pytest_asyncio.fixture(scope="function")
async def editor_user(db_session: AsyncSession) -> User:
    """Create and persist a test editor user."""
    user = User(
        id=UserId(uuid.uuid4()),
        email="editor@test.com",
        display_name="Test Editor",
        password_hash=hash_password("Test1234!"),
        role=UserRole.EDITOR,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def viewer_user(db_session: AsyncSession) -> User:
    """Create and persist a test viewer user."""
    user = User(
        id=UserId(uuid.uuid4()),
        email="viewer@test.com",
        display_name="Test Viewer",
        password_hash=hash_password("Test1234!"),
        role=UserRole.VIEWER,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def editor_token(editor_user: User, test_settings: Settings) -> str:
    """Return a valid access token for the editor user."""
    return create_access_token(editor_user.email, test_settings)


@pytest.fixture(scope="function")
def viewer_token(viewer_user: User, test_settings: Settings) -> str:
    """Return a valid access token for the viewer user."""
    return create_access_token(viewer_user.email, test_settings)


@pytest.fixture(scope="function")
def auth_headers(editor_token: str) -> dict[str, str]:
    """Return Authorization headers for the editor user."""
    return {"Authorization": f"Bearer {editor_token}"}
