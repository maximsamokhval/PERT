from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger


def setup_logging(level: str = "INFO") -> None:
    """Configure loguru structured logging.

    Outputs human-readable logs to stdout and JSON-serialized logs to
    logs/app.log. This function must be called once during app startup.
    """
    logger.remove()

    # Human-readable stdout output
    logger.add(
        sys.stdout,
        level=level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # Structured JSON log file (machine-readable)
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    logger.add(
        log_dir / "app.log",
        level=level,
        rotation="10 MB",
        retention="7 days",
        compression="gz",
        serialize=True,  # JSON format for log aggregation
        backtrace=False,
        diagnose=False,
    )


# Re-export logger so feature modules import from here, not loguru directly
__all__ = ["logger", "setup_logging"]
