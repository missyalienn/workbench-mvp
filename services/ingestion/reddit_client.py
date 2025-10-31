import keyring
from config.logging_config import configure_logging, get_logger
from praw import Reddit

# Configure logging handler 
configure_logging()
logger = get_logger(__name__)

def get_reddit_client() -> Reddit:
    """Return an authenticated Reddit client using keyring credentials."""
    client_id = keyring.get_password("reddit-client-id", "dev")
    client_secret = keyring.get_password("reddit-client-secret", "dev")
    user_agent = "TestScript/1.0 by /u/chippetto90"

    if not all([client_id, client_secret]):
        msg = "Missing Reddit credentials in keyring for environment: dev"
        logger.error(msg)
        raise RuntimeError(msg)

    logger.info("Reddit client authenticated via keyring.")
    return Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)

# ---------------- RUN BLOCK ----------------
if __name__ == "__main__":
    try:
        get_reddit_client()
    except Exception:
        logger.exception("Failed to initialize Reddit client.")