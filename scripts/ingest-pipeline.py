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

def fetch_posts(reddit, limit=1000):
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
    """Build structured dataset from posts and their comments."""
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
        
        # Clean comments
        clean_comments = [clean_text(comment.body) for comment in comments if clean_text(comment.body)]
        
        # Create post entry
        post_entry = {
            'post_id': submission.id,
            'post_text': post_text,
            'comments': clean_comments,
            'score': submission.score,
            'permalink': f"https://reddit.com{submission.permalink}",
        }
        
        dataset.append(post_entry)
    
    print(f"Dataset built with {len(dataset)} posts")
    return dataset

def save_json(dataset, filename="reddit_data.json", batch_size=100):
    """Save dataset to JSON file in batches."""
    print(f"Saving dataset to {filename} in batches of {batch_size}...")
    
    # Initialize JSON file with opening bracket
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('[\n')
    
    # Process dataset in batches
    for i in range(0, len(dataset), batch_size):
        batch = dataset[i:i + batch_size]
        
        # Append batch to file
        with open(filename, 'a', encoding='utf-8') as f:
            for j, post in enumerate(batch):
                # Add comma after each post except the last one in the entire dataset
                is_last_post = (i + j == len(dataset) - 1)
                json.dump(post, f, indent=2, ensure_ascii=False)
                if not is_last_post:
                    f.write(',')
                f.write('\n')
        
        print(f"Saved batch {i//batch_size + 1}/{(len(dataset) + batch_size - 1)//batch_size} ({len(batch)} posts)")
    
    # Close JSON array
    with open(filename, 'a', encoding='utf-8') as f:
        f.write(']')
    
    print(f"Dataset saved to {filename} ({len(dataset)} total posts)")

def main():
    """Main function to orchestrate the Reddit data pipeline."""
    print("Starting Reddit data pipeline...")
    print(f"User Agent: {user_agent}")
    
    # Test Reddit connection
    try:
        reddit.user.me()
        print("Reddit API authentication successful.")
    except Exception as e:
        print(f"Reddit API authentication failed: {e}")
        return
    
    # Fetch posts
    posts_list = fetch_posts(reddit, limit=1000)
    
    # Build dataset
    dataset = build_dataset(posts_list, comment_limit=10)
    
    # Save to JSON
    save_json(dataset, filename="reddit_data.json")
    
    print("Pipeline completed successfully!")

if __name__ == "__main__":
    main()