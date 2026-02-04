"""Logging configuration."""

import logging
import sys


def setup_logging(
    debug: bool = False,
    log_level: str | None = None,
) -> None:
    """Configure application logging.

    Called at app startup so all log levels (including DEBUG) are visible
    when DEBUG=true or LOG_LEVEL=DEBUG (e.g. in Docker).

    Args:
        debug: If True, set log level to DEBUG (overrides log_level).
        log_level: Level name: DEBUG, INFO, WARNING, ERROR. Used when debug is False.
    """
    if debug:
        level = logging.DEBUG
    elif log_level:
        level = getattr(logging, log_level.upper(), logging.INFO)
    else:
        level = logging.INFO

    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    root_logger.setLevel(level)
    root_logger.addHandler(handler)

    logging.getLogger("uvicorn").setLevel(level)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(level)
    logging.getLogger("apex").setLevel(level)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
