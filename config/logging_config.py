import logging
from config.settings import settings

def configure_logging() -> None:
    """Configure project-wide logging settings."""
    numeric_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    logging.basicConfig(
        level=numeric_level,
        format=settings.LOG_FORMAT,
        datefmt=settings.LOG_DATE_FORMAT,
        force=True,
    )
    # Confirmation message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured at {settings.LOG_LEVEL.upper()} level.")

def get_logger(name: str) -> logging.Logger:
    """Return a named logger for a given module."""
    return logging.getLogger(name)


if __name__ == "__main__":
    configure_logging()
    log = get_logger(__name__)
    log.info("Info message (should always appear).")
    log.debug("Debug message (appears only if LOG_LEVEL=DEBUG).")

