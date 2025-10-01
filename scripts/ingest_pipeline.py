import os 
import praw
import json
import time
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Reddit API credentials from .env file
client_id = os.getenv('REDDIT_CLIENT_ID')
client_secret = os.getenv('REDDIT_CLIENT_SECRET')
user_agent = os.getenv('REDDIT_USER_AGENT') or "TestScript/1.0 by /u/chippetto90"

# Initialize Reddit client
reddit = praw.Reddit(
    client_id=client_id,
    client_secret=client_secret,
    user_agent=user_agent,
)

def fetch_posts(reddit, limit=10):
    """Fetch top posts from r/diy subreddit with rate limiting."""
    print(f"Fetching top {limit} posts from r/diy...")
    posts_list = []
    subreddit = reddit.subreddit("diy")
    
    for i, submission in enumerate(subreddit.top(time_filter="year", limit=limit)):
        posts_list.append(submission)
        if (i + 1) % 100 == 0:
            print(f"Fetched {i + 1} posts...")
        time.sleep(1.2)  # Respect Reddit API limits
    
    print(f"Successfully fetched {len(posts_list)} posts")
    return posts_list

def fetch_comments(submission, limit=10):
    """Fetch top comments for a given submission."""
    try:
        # Expand "MoreComments" objects to access all comments with threshold filtering
        submission.comments.replace_more(limit=0, threshold=3)
        # Use .list() to get flattened comment structure and slice to limit
        return list(submission.comments.list()[:limit])
    except Exception as e:
        print(f"Error fetching comments for post {submission.id}: {e}")
        return []

def clean_text(text):
    """Clean text by removing URLs, markdown formatting, and normalizing whitespace."""
    if not text:
        return ""
    
    # Remove URLs
    text = re.sub(r'https?://\S+', '', text)
    # Remove markdown links but keep the text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # Remove bold markdown
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    # Remove italic markdown
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    # Remove strikethrough
    text = re.sub(r'~~([^~]+)~~', r'\1', text)
    # Remove code blocks
    text = re.sub(r'`([^`]+)`', r'\1', text)
    # Normalize whitespace and remove newlines
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def build_dataset(posts_list, comment_limit=10):
    """Build flat dataset from posts and their comments."""
    print("Building dataset...")
    dataset = []
    
    for i, submission in enumerate(posts_list):
        # Get comments for this post
        comments = fetch_comments(submission, comment_limit)
        
        # Clean post title and content
        clean_title = clean_text(submission.title)
        clean_content = clean_text(submission.selftext)
        
        # Combine title and content
        post_text = f"{clean_title} {clean_content}".strip()
        
        # Create post record (flat structure)
        post_record = {
            'id': f"post_{submission.id}",
            'type': 'post',
            'text': post_text,
            'score': submission.score,
            'source': 'reddit',
            'url': f"https://reddit.com{submission.permalink}",
            'created_at': submission.created_utc
        }
        dataset.append(post_record)
        
        # Create comment records (flat structure)
        for comment in comments:
            clean_comment_text = clean_text(comment.body)
            if clean_comment_text:  # Only add non-empty comments
                comment_record = {
                    'id': f"comment_{comment.id}",
                    'type': 'comment',
                    'text': clean_comment_text,
                    'score': comment.score,
                    'link_id': f"post_{submission.id}",
                    'source': 'reddit',
                    'created_at': comment.created_utc
                }
                dataset.append(comment_record)
    
    print(f"Dataset built with {len(dataset)} records")
    return dataset

def save_jsonl(dataset, filename="reddit_data.jsonl", batch_size=100):
    """Save dataset to JSONL file in batches."""
    print(f"Saving dataset to {filename} in batches of {batch_size}...")
    
    # Clear the file first
    with open(filename, 'w', encoding='utf-8') as f:
        pass
    
    # Process dataset in batches
    for i in range(0, len(dataset), batch_size):
        batch = dataset[i:i + batch_size]
        
        # Append batch to file (one JSON object per line)
        with open(filename, 'a', encoding='utf-8') as f:
            for record in batch:
                json.dump(record, f, ensure_ascii=False)
                f.write('\n')  # One record per line
        
        print(f"Saved batch {i//batch_size + 1}/{(len(dataset) + batch_size - 1)//batch_size} ({len(batch)} records)")
    
    print(f"Dataset saved to {filename} ({len(dataset)} total records)")

def main():
    """Main function to orchestrate the Reddit data pipeline."""
    print("Starting Reddit data pipeline...")
    print(f"User Agent: {user_agent}")
    
    # Test Reddit connection with actual data fetch
    try:
        # Test with a small data fetch to validate credentials
        subreddit = reddit.subreddit("diy")
        test_posts = list(subreddit.hot(limit=1))  # Just 1 post to test
        
        if test_posts:
            print("Reddit API authentication successful.")
        else:
            print("Reddit API authentication failed: No posts returned")
            return
            
    except Exception as e:
        print(f"Reddit API authentication failed: {e}")
        print("Check your REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env")
        return
    
    # Fetch posts
    posts_list = fetch_posts(reddit, limit=10)
    
    # Build dataset
    dataset = build_dataset(posts_list, comment_limit=10)
    
    # Save to JSONL
    save_jsonl(dataset, filename="reddit_data.jsonl")
    
    print("Pipeline completed successfully!")

if __name__ == "__main__":
    main()