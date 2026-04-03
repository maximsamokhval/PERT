from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .core.db import dispose_db, init_db
from .core.logging import setup_logging
from .features.auth.routes import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: initialize resources on startup, dispose on shutdown."""
    settings = get_settings()
    setup_logging(level=settings.log_level)
    init_db(settings.database_url, echo=settings.debug)
    yield
    await dispose_db()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="PERT Estimation SDLC Tool",
        description="API for PERT-based estimation sessions and YouTrack export",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)

    @app.get("/health", tags=["infra"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
