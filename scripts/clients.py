"""Purpose: centralize auth + client creation for external services."""

import keyring
from openai import OpenAI
from pinecone import Pinecone
from praw import Reddit 

def get_openai_client():
    #Return an authenticated OpenAI client 
    api_key = keyring.get_password("openai-key", "dev")
    return OpenAI(api_key=api_key)

def get_pinecone_client():
    #Return an authenticated Pinecone client 
    pc_key = keyring.get_password("pinecone-api-key", "dev")
    return Pinecone(api_key=pc_key)

def get_reddit_client():
    #Return an authenticated Reddit client 
    client_id = keyring.get_password("reddit-client-id", "reddit-api")
    client_secret = keyring.get_password("reddit-client-secret", "reddit-api")
    user_agent = "TestScript/1.0 by /u/chippetto90"
    return Reddit(client_id=client_id,client_secret=client_secret,user_agent=user_agent)
