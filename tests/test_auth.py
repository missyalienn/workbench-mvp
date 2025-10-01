#Quick sanity test for reddit auth for ingestion pipeline
import praw 
import keyring 
import openai

#Test reddit auth 

def test_reddit_auth():
    client_id = keyring.get_password("reddit-client-id", "reddit-api")
    client_secret = keyring.get_password("reddit-client-secret", "reddit-api")
    user_agent = "TestScript/1.0 by /u/chippetto90"

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
        read_only=True,
    )
    posts = list(reddit.subreddit("diy").hot(limit=1))
    assert posts, "Reddit auth failed"
    print("Retrieved post:", posts[0].title)

#Test openai auth 

#def test_openai_auth():
    # assumes your key is stored in Keychain under service "openai" / user "api-key"
    #api_key = keyring.get_password("openai", "api-key")
    #openai.api_key = api_key

    #resp = openai.embeddings.create(
        #model="text-embedding-3-small",
        #input="hello world"
    #)
    #assert "data" in resp and len(resp.data) > 0, "OpenAI auth failed"
