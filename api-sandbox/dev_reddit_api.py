#Reddit API sandbox

import os
from random import sample 
import praw
import keyring 
from dotenv import load_dotenv
from praw.models import user
import time

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


#Fetch top posts by subreddit flair
def fetch_posts_by_flair(reddit, limit=5, sample_size=50, delay=0.5):
    """
    Fetch top posts from r/diy filtered for a given flair ("home improvement", "help", etc)
    Prints each matching post while fetching.
    """
    posts_list = []
    subreddit = reddit.subreddit("diy")
    
    print(f"Fetching up to {limit} posts from r/diy with flair: help. Sampling {sample_size} top posts)...\n")
    
    for submission in subreddit.top(time_filter="year", limit=sample_size):
        if submission.link_flair_text and submission.link_flair_text.lower() == "help":
            posts_list.append(submission)
            print(f"- {submission.title[:80]} | Flair: {submission.link_flair_text}")
            if len(posts_list) >= limit:
                break
        time.sleep(delay)  # Respect Reddit API limits
    
    print(f"\nFinished! Collected {len(posts_list)} posts.\n")
    return posts_list
    
fetch_posts_by_flair(reddit)





#Return the flair structure for a subreddit (r/diy)
def test_flair_structure(reddit):
    subreddit = reddit.subreddit('diy')
    
    for i, post in enumerate(subreddit.new(limit=5)):
        print(f"Post {i+1}:")
        print(f"  Title: {post.title[:50]}...")
        print(f"  Flair Text: {getattr(post, 'link_flair_text', None)}")
        print(f"  Flair Template ID: {getattr(post, 'link_flair_template_id', None)}")
        print(f"  Flair CSS Class: {getattr(post, 'link_flair_css_class', None)}")
        print("-" * 30)

#test_flair_structure(reddit)

