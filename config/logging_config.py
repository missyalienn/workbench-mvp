import os
import logging

# -- Read log level from .env or fallback -- 
level_name = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_LEVEL = getattr(logging, level_name, logging.INFO)

# -- Setup -- 
def configure_logging(): 
    logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
    )
    
# --Helper function for modules--
def get_logger(name):
    return logging.getLogger(name)

# -- Example --
if __name__ == "__main__":
    configure_logging()
    log = get_logger(__name__)
    log.info("info message")
    log.debug("debug message")