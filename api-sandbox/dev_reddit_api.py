#Reddit API sandbox

import os 
import praw
import keyring 
from dotenv import load_dotenv
from praw.models import user

#load_dotenv()

#Get Reddit API Key from Keychain 
client_id = keyring.get_password("reddit-client-id", "reddit-api")
client_secret = keyring.get_password("reddit-client-secret", "reddit-api")
user_agent = "TestScript/1.0 by /u/chippetto90"

# Initialize Reddit client
reddit = praw.Reddit(
    client_id=client_id,
    client_secret=client_secret,
    user_agent=user_agent,
)

print("User agent:", user_agent)

#OLD .env + shell Method: 
#Get Reddit API credentials from .env file
#client_id = os.getenv('REDDIT_CLIENT_ID')
#client_secret = os.getenv('REDDIT_CLIENT_SECRET')
#user_agent = os.getenv('REDDIT_USER_AGENT') or "TestScript/1.0 by /u/chippetto90"





