
import os
from random import sample 
import praw
import keyring 
import time

# Reddit API Auth using Keychain Creds 
client_id = keyring.get_password("reddit-client-id", "reddit-api")
client_secret = keyring.get_password("reddit-client-secret", "reddit-api")
user_agent = "TestScript/1.0 by /u/chippetto90"

# Initialize Reddit client
reddit = praw.Reddit(
    client_id=client_id,
    client_secret=client_secret,
    user_agent=user_agent,
)


def fetch_flair_posts(
    reddit, 
    subreddit_name="diy", 
    flair=None, 
    limit=10, 
    sample_size=50, 
    keywords=None,
    delay=0.5 #default sleep between requests
):
    """
    Fetch top posts from a subreddit filtered by flair and optional title keywords.
    
    Parameters:
    - reddit: authenticated PRAW Reddit instance
    - subreddit_name: subreddit to fetch from (default 'diy')
    - flair: text of the flair to filter by (case-insensitive)
    - limit: max number of posts to return
    - sample_size: number of top posts to sample from
    - keywords: list of keywords to filter titles (case-insensitive)
    
    Returns:
    - List of PRAW Submission objects
    """
    posts_list = []
    subreddit = reddit.subreddit(subreddit_name)
    
    if keywords is None:
        keywords = []  # empty list means no keyword filtering

    print(f"Fetching up to {limit} posts from {subreddit_name} with flair: {flair}. Sample size = {sample_size} top posts...\n")
    
    for submission in subreddit.top(time_filter="year", limit=sample_size):
        title_lower = submission.title.lower()
        flair_match = (flair is None) or (submission.link_flair_text and submission.link_flair_text.lower() == flair.lower())
        keyword_match = (not keywords) or any(kw.lower() in title_lower for kw in keywords)
        
        if flair_match and keyword_match:
            posts_list.append(submission)
            if len(posts_list) >= limit:
                break
        time.sleep(delay)  # Respect Reddit API rate limits

    print(f"\nDone! Collected {len(posts_list)} posts.\n")
    return posts_list

#Fetch flair home improvement top 10 sample 100 
posts = fetch_flair_posts(
    reddit, 
    flair="home improvement",
    keywords=None,
    limit=10, 
    sample_size=100,
    delay=0.3
)

for post in posts: 
     print(f"- {post.title[:80]} | Flair: {post.link_flair_text}")

#Fetch flair help top 10 sample 100
posts = fetch_flair_posts(
    reddit, 
    flair="help",
    keywords=None,
    limit=10, 
    sample_size=100
)

for post in posts: 
     print(f"- {post.title[:80]} | Flair: {post.link_flair_text}")


#Keyword Filtering Test with Stats (Test keyword "My")
subreddit = reddit.subreddit("diy")
sample_posts = list(subreddit.top(time_filter="year", limit=20))  # small sample for testing

# Keywords to Test: 
keywords = ["my"]  # just to see if filtering works

# Track matches
matches = []

for post in sample_posts:
    match = any(kw.lower() in post.title.lower() for kw in keywords)
    matches.append(match)
    print(f"Title: {post.title[:60]} | Match: {match}")

# Calculate stats
total = len(matches)
true_count = sum(matches)
percent_true = true_count / total * 100 if total else 0

print("\nSummary:")
print(f"Total posts sampled: {total}")
print(f"Posts matching keyword: {true_count}")
print(f"Percent matching: {percent_true:.1f}%")


#**Home Improvement Flair (Top 100 posts)**  
#Returned 10 posts, but most were project showcases rather than instructional/how-to content.  
#**Help Flair (Top 100 posts)** Returned 5 posts.  Some were actual questions or "how-to" style, others were situational/context-based.  

#Key Takeaways:**  
#Flair-only filtering works but **does not guarantee instructional content**.  
# Some flairs (like "help") are **sparse in top posts**, limiting relevant content.  
#To improve recall, consider **combining flair + keyword search in title and body** or using **PRAW search queries** directly.