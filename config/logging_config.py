import logging
import os

def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        force=True,
    )

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


if __name__ == "__main__":
    configure_logging()
    log = get_logger(__name__)
    log.info("info message")
    log.debug("debug message")
