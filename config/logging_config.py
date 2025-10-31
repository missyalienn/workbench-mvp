import logging
import os

def configure_logging() -> None:
    """Configure project-wide logging settings."""

    # Read level from .env; default to INFO is missing or invalid 
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    numeric_level = getattr(logging, log_level, logging.INFO)

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        force=True,
    )

def get_logger(name: str) -> logging.Logger:
    """Return a named logger for a given module."""
    return logging.getLogger(name)


if __name__ == "__main__":
    configure_logging()
    log = get_logger(__name__)
    log.info("Info message (should always appear).")
    log.debug("Debug message (appears only if LOG_LEVEL=DEBUG).")
