from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def _make_file_handler(log_file: str | Path) -> RotatingFileHandler:
    path = Path(log_file)
    path.parent.mkdir(parents=True, exist_ok=True)

    return RotatingFileHandler(
        filename=path,
        maxBytes=2_000_000,
        backupCount=3,
        encoding="utf-8",
    )


def _reset_all_known_loggers() -> None:
    """Remove handlers that could have been installed by uvicorn/apscheduler/etc."""

    root = logging.getLogger()
    root.handlers.clear()

    for logger_name in (
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "apscheduler",
        "apscheduler.scheduler",
        "apscheduler.executors.default",
        "health_agent",
    ):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.propagate = True


def setup_mcp_logging(
    *,
    log_file: str | Path = "logs/mcp.log",
    level: int = logging.INFO,
) -> None:
    """Configure logging for the MCP stdio process.

    MCP may be launched as a child process by PicoClaw. File logging is the
    important sink here. Console logging is intentionally not required.
    """

    _reset_all_known_loggers()

    file_handler = _make_file_handler(log_file)

    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        handlers=[file_handler],
        force=True,
    )

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def setup_api_logging(
    *,
    log_file: str | Path = "logs/api.log",
    level: int = logging.INFO,
    console: bool = False,
) -> None:
    """Configure logging for the FastAPI + Uvicorn + APScheduler process.

    Uvicorn normally installs its own console loggers. This setup clears them
    and routes uvicorn/apscheduler/application logs through the root logger.
    """

    _reset_all_known_loggers()

    handlers: list[logging.Handler] = [_make_file_handler(log_file)]

    if console:
        handlers.append(logging.StreamHandler(sys.stdout))

    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        handlers=handlers,
        force=True,
    )

    # Keep noisy libraries quiet.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    # Make sure these loggers do not keep their own console handlers.
    for logger_name in (
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "apscheduler",
        "apscheduler.scheduler",
        "apscheduler.executors.default",
    ):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.propagate = True
        logger.setLevel(level)