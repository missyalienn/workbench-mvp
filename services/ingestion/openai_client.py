import keyring 
from config.logging_config import configure_logging, get_logger

from openai import OpenAI

# Configure logging handler 
configure_logging()
logger = get_logger(__name__)

def get_openai_client() -> OpenAI: 
    "Return an authenticated OpenAI client using keyring credentials."""
    api_key = keyring.get_password("openai-key", "dev")

    if not api_key: 
        msg = "Missing OpenAI credentials in keyring for environment: dev."
        logger.error(msg)
        raise RuntimeError(msg)

    logger.info("Initalized OpenAI client.")
    return OpenAI(api_key=api_key)

# ---------------- RUN BLOCK ----------------
if __name__ == "__main__":
    try:
        get_openai_client()
    except Exception:
        logger.exception("Failed to initialize OpenAI client.")