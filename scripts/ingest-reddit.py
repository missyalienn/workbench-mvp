
import os 
import praw
import time 
import json 
import re
from dotenv import load_dotenv

# Load .env from project root
load_dotenv('.env')

# get credentials from environment variables
client_id = os.getenv('REDDIT_CLIENT_ID')
client_secret = os.getenv('REDDIT_CLIENT_SECRET')
user_agent = os.getenv('REDDIT_USER_AGENT') or "TestScript/1.0 by /u/yourusername"

#print(f"Client ID: {client_id}")
print(f"User Agent: {user_agent}")

# authenticate with Reddit
reddit = praw.Reddit(
    client_id=client_id,
    client_secret=client_secret,
    user_agent=user_agent,
)
#Test the connection
print("Reddit API authentication successful.")

#Create connection to r/diy
subreddit = reddit.subreddit("diy")

# Create an empty list to store all post data
all_data = []  
post_counter = 1

# DATA STRUCTURE EXPLANATION:
# submission = Reddit API object (from PRAW) - contains raw Reddit post data
# reddit_post = Dictionary we create to store organized post data
# all_data = List that stores all reddit_post dictionaries
# post (in cleaning loop) = Each individual reddit_post dictionary from all_data
# comment (in cleaning loop) = Each individual comment dictionary within a post

#For top 10 posts from r/diy last month, create a dictionary to store post data 
for submission in reddit.subreddit("diy").top(time_filter="month", limit=10):
    
    # Create a dictionary to store post data
    reddit_post = {
        'post_id': submission.id,
        'title': submission.title,
        'content': submission.selftext,
        'score': submission.score,
        'permalink': f"https://reddit.com{submission.permalink}",
        'comments': []  # Store comments in a list for this post
    }
    
    # Get comments FOR THIS SPECIFIC POST
    submission.comments.replace_more(limit=0)
    for i, comment in enumerate(submission.comments):
        if i >= 5:  # Stop after 5 comments
            break
        # Store comment data WITH reference to this post
        comment_data = {
            'post_id': submission.id,  # Link back to parent post
            'comment_id': comment.id,
            'body': comment.body,
            'score': comment.score
        }
        reddit_post['comments'].append(comment_data)
    
    all_data.append(reddit_post)
    time.sleep(1.2)
  
    print(f"Processed post:{post_counter} - {submission.title[:50]}...")
    print(f"Stored top {len(reddit_post['comments'])} comments")
    post_counter += 1

#Clean and normalize post and comment text 
for post in all_data: 
    # Clean and normalize post title and content
    raw_title = post['title']  # Get raw title
    raw_content = post['content']  # Get raw content
    text = f"{raw_title} {raw_content}"  # Combine title and content
    text = re.sub(r'https?://\S+', '', text)  # Remove URLs
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # Remove markdown links
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Remove bold markdown
    text = re.sub(r'\*([^*]+)\*', r'\1', text)  # Remove italic markdown
    text = re.sub(r'~~([^~]+)~~', r'\1', text)  # Remove strikethrough
    text = re.sub(r'\s+', ' ', text).strip()  # Normalize whitespace
    post['clean_text'] = text  # Store cleaned text

    # Clean and normalize each comment body
    for comment in post['comments']:
        c_text = comment['body']  # Get raw comment text
        c_text = re.sub(r'https?://\S+', '', c_text)  # Remove URLs
        c_text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', c_text)  # Remove markdown links
        c_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', c_text)  # Remove bold markdown
        c_text = re.sub(r'\*([^*]+)\*', r'\1', c_text)  # Remove italic markdown
        c_text = re.sub(r'~~([^~]+)~~', r'\1', c_text)  # Remove strikethrough
        c_text = re.sub(r'\s+', ' ', c_text).strip()  # Normalize whitespace
        comment['clean_body'] = c_text  # Store cleaned comment text



    # Save to JSON file
    #with open('reddit-test-data.json', 'w') as f:
        #json.dump(all_data, f, indent=4)