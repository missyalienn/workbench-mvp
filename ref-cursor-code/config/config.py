"""
config.py
Secure credential retrieval for OpenAI and Reddit API access.

This module uses macOS Keychain via `keyring` library to fetch secrets.
No secrets are stored in plaintext or shell environment variables.

.env is used only for metadata—specifying which Keychain service and account to query.
If Keychain lookup fails, system fails loudly. Currently no fallback to .env values.
"""

import keyring
import os
from dotenv import load_dotenv

load_dotenv()

def get_openai_key():
    service = os.getenv("OPENAI_KEYCHAIN_SERVICE", "openai-key")
    account = os.getenv("OPENAI_KEYCHAIN_ACCOUNT", "dev")
    key = keyring.get_password(service, account)
    if not key:
        raise ValueError("OpenAI API key not found in Keychain.")
    return key

def get_reddit_credentials():
    client_id = keyring.get_password("reddit-client-id", "reddit-api")
    client_secret = keyring.get_password("reddit-client-secret", "reddit-api")
    user_agent = os.getenv("REDDIT_USER_AGENT")

    if not all([client_id, client_secret, user_agent]):
        raise ValueError("Missing Reddit credentials. Check Keychain and .env setup.")

    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "user_agent": user_agent
    }