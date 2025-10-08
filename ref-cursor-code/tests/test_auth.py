#Quick sanity test for reddit auth for ingestion pipeline
import praw 
import keyring 
from openai import OpenAI
import pytest

#Test reddit auth 
def test_reddit_auth():
    client_id = keyring.get_password("reddit-client-id", "reddit-api")
    client_secret = keyring.get_password("reddit-client-secret", "reddit-api")
    user_agent = "TestScript/1.0 by /u/chippetto90"

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )
    assert reddit.read_only, "Reddit auth failed"

#Test openai auth 
def test_openai_auth():
    api_key = keyring.get_password("openai-key", "dev")
    client = OpenAI(api_key=api_key)

    models = client.models.list()
    assert models.data and len(models.data) > 0, "OpenAI auth failed. "

  

#pytest tests/test_auth.py::test_reddit_auth - v
#pytest tests/test_auth.py::test_openai_auth - v
#@pytest.mark.skip(reason="Temporarily disabled while working on auth flow")   