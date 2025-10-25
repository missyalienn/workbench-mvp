import logging

import keyring
from praw import Reddit

logger = logging.getLogger(__name__)

def get_reddit_client() -> Reddit:
    """Return an authenticated Reddit client using keyring credentials."""
    client_id = keyring.get_password("reddit-client-id", "reddit-api")
    client_secret = keyring.get_password("reddit-client-secret", "reddit-api")
    user_agent = "TestScript/1.0 by /u/chippetto90"

    if not all([client_id, client_secret]):
        msg = "Missing Reddit credentials in keyring (service: reddit-api)"
        logger.error(msg)
        raise RuntimeError(msg)

    logger.info("Reddit client authenticated via keyring.")
    return Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)