import logging
from contextvars import ContextVar
from contextlib import contextmanager
from typing import Optional
from config.settings import settings
import json
from datetime import datetime

_plan_id_context: ContextVar[Optional[str]] = ContextVar('plan_id_context', default=None)


class PlanIdFormatter(logging.Formatter):
    """Formatter that includes plan_id from context when available."""
    def format(self, record: logging.LogRecord) -> str:
        plan_id = _plan_id_context.get()
        record.plan_id = f"[plan_id={plan_id}]" if plan_id else ""
        return super().format(record)


class PlanIdJsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        plan_id = _plan_id_context.get()
        output = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "plan_id": plan_id or None,
        }
        return json.dumps(output)


def configure_logging() -> None:
    """Configure project-wide logging settings."""
    numeric_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    logging.basicConfig(
        level=numeric_level,
        format=settings.LOG_FORMAT,
        datefmt=settings.LOG_DATE_FORMAT,
        force=True,
    )
    
    # Choose formatter based on LOG_FORMAT_TYPE
    formatter: logging.Formatter
    if settings.LOG_FORMAT_TYPE == "json":
        formatter = PlanIdJsonFormatter()
    else:
        formatter = PlanIdFormatter(settings.LOG_FORMAT, settings.LOG_DATE_FORMAT)
    for handler in logging.root.handlers:
        handler.setFormatter(formatter)
    
    # Suppress noisy third-party library logs
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("keyring.backend").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured at {settings.LOG_LEVEL.upper()} level.")


def get_logger(name: str) -> logging.Logger:
    """Return a named logger for a given module."""
    return logging.getLogger(name)


@contextmanager
def plan_context_scope(plan_id: str):
    """Context manager for plan_id traceability across agent steps."""
    token = _plan_id_context.set(plan_id)
    try:
        yield
    finally:
        _plan_id_context.reset(token)


if __name__ == "__main__":
    configure_logging()
    log = get_logger(__name__)
    log.info("Info message (should always appear).")
    log.debug("Debug message (appears only if LOG_LEVEL=DEBUG).")

