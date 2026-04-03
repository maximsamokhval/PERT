from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables / .env file.

    This is the SOLE configuration entry point for the application.
    All other modules receive settings exclusively via FastAPI Depends() —
    never via a module-level get_settings() call.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "sqlite+aiosqlite:///./pert.db"

    # Encryption (Fernet key for TrackerConnection.token_encrypted)
    encryption_key: str = ""

    # JWT
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    # CORS (comma-separated list of allowed origins)
    cors_origins: str = "http://localhost:3000"

    # Logging
    log_level: str = "INFO"

    # Debug mode — enables SQLAlchemy echo and verbose error details
    debug: bool = False

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_sqlite(self) -> bool:
        return "sqlite" in self.database_url


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance. Use only via FastAPI Depends()."""
    return Settings()
