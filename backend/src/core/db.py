from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy declarative base. All ORM models inherit from this."""

    pass


# Module-level engine and session factory — initialized once during app startup
# via init_db(). Using None guards prevent access before initialization.
_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def _set_sqlite_pragmas(dbapi_conn: object, connection_record: object) -> None:
    """Enable WAL mode and foreign key enforcement for SQLite connections."""
    # dbapi_conn is the raw DBAPI connection; we call execute directly on it
    import sqlite3  # noqa: PLC0415

    if isinstance(dbapi_conn, sqlite3.Connection):
        dbapi_conn.execute("PRAGMA journal_mode=WAL")
        dbapi_conn.execute("PRAGMA synchronous=NORMAL")
        dbapi_conn.execute("PRAGMA foreign_keys=ON")


def init_db(database_url: str, *, echo: bool = False) -> AsyncEngine:
    """Initialize the async database engine and session factory.

    Must be called exactly once during application startup (lifespan).
    After this call, get_db() is safe to use as a FastAPI dependency.
    """
    global _engine, _async_session_factory  # noqa: PLW0603

    _engine = create_async_engine(
        database_url,
        echo=echo,
        connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
    )

    if "sqlite" in database_url:
        event.listen(_engine.sync_engine, "connect", _set_sqlite_pragmas)

    _async_session_factory = async_sessionmaker(
        _engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    return _engine


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session.

    Usage in routes:
        db: Annotated[AsyncSession, Depends(get_db)]
    """
    if _async_session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() in app lifespan.")
    async with _async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def check_db_connection() -> bool:
    """Health check — returns True if the database is reachable."""
    if _engine is None:
        return False
    try:
        async with _engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def dispose_db() -> None:
    """Dispose the engine connection pool. Call during app shutdown."""
    if _engine is not None:
        await _engine.dispose()
