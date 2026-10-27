"""structlog setup: `configure_logging()` once at startup, `get_logger(name)` everywhere."""

import logging

import structlog

from app.config.settings import settings


def configure_logging() -> None:
    """Configure structlog and stdlib logging. LOG_FORMAT_TYPE=json for structured output."""
    numeric_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    renderer: structlog.types.Processor
    if settings.LOG_FORMAT_TYPE == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Stdlib config so third-party libs still emit.
    logging.basicConfig(level=numeric_level, format="%(levelname)s %(name)s %(message)s", force=True)

    for lib in ("openai", "httpcore", "httpx", "urllib3", "markdown_it"):
        logging.getLogger(lib).setLevel(logging.WARNING)

    get_logger(__name__).info(
        "logging.configured", level=settings.LOG_LEVEL.upper(), format=settings.LOG_FORMAT_TYPE
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Return a named structlog bound logger."""
    return structlog.get_logger(name)
