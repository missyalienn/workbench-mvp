#openai API sandbox

from openai import OpenAI
import os
import keyring
from dotenv import load_dotenv
#load_dotenv()


# Get OpenAI API key from Keychain
api_key = keyring.get_password("openai-key", "dev")

def test_openai_auth():
    api_key = keyring.get_password("openai-key", "dev")
    client = OpenAI(api_key=api_key)

    models = client.models.list()
    assert models.data and len(models.data) > 0, "OpenAI auth failed. "
    