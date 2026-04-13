"""Logging configuration using structlog.

Provides:
    configure_logging() — call once at application startup
    get_logger(name)    — returns a structlog bound logger
    plan_context_scope(plan_id) — context manager that binds plan_id to all logs
"""

import logging
from contextlib import contextmanager

import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars

from config.settings import settings


def configure_logging() -> None:
    """Configure structlog and stdlib logging for the project.

    Text mode (default): human-readable output via ConsoleRenderer.
    JSON mode (LOG_FORMAT_TYPE=json): structured JSON output.

    Call once at application startup (entrypoint or script top-level).
    """
    numeric_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Shared processors for both stdlib and structlog paths.
    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if settings.LOG_FORMAT_TYPE == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    # Configure structlog globally.
    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure stdlib logging so third-party libs (openai, httpx, etc.) still emit.
    logging.basicConfig(
        level=numeric_level,
        format="%(levelname)s %(name)s %(message)s",
        force=True,
    )

    # Suppress noisy third-party loggers.
    for lib in ("openai", "httpcore", "httpx", "keyring.backend", "urllib3", "markdown_it"):
        logging.getLogger(lib).setLevel(logging.WARNING)

    # Fetcher rejection logs are DEBUG — visible only when LOG_LEVEL=DEBUG.
    logging.getLogger("services.fetch.comment_pipeline").setLevel(logging.DEBUG)

    logger = get_logger(__name__)
    logger.info("logging.configured", level=settings.LOG_LEVEL.upper(), format=settings.LOG_FORMAT_TYPE)


def get_logger(name: str) -> structlog.BoundLogger:
    """Return a named structlog bound logger."""
    return structlog.get_logger(name)


@contextmanager
def plan_context_scope(plan_id: str):
    """Bind plan_id to all log lines emitted within this context."""
    bind_contextvars(plan_id=plan_id[:8])
    try:
        yield
    finally:
        clear_contextvars()


if __name__ == "__main__":
    configure_logging()
    log = get_logger(__name__)
    log.info("logging.test", msg="Info message (should always appear).")
    log.debug("logging.test", msg="Debug message (appears only if LOG_LEVEL=DEBUG).")
