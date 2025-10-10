import os 
import praw
import json
import time
import re
from html import unescape
from html.parser import HTMLParser
from markdown_it import MarkdownIt
from dotenv import load_dotenv
import keyring

# Load environment variables
load_dotenv()

#Get Reddit API creds from KeyRing
client_id = keyring.get_password("reddit-client-id", "reddit-api")
client_secret = keyring.get_password("reddit-client-secret", "reddit-api")
user_agent = "TestScript/1.0 by /u/chippetto90"

ALLOWED_FLAIRS = {"help", "question", "advice", "how to"}
TITLE_KEYWORDS = ("how", "what", "why", "can", "should", "best way", "need help")

markdown_parser = MarkdownIt()
URL_PATTERN = re.compile(r'https?://\S+', re.I)
WHITESPACE_PATTERN = re.compile(r'\s+')

class _MarkdownTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._chunks = []

    def handle_data(self, data):
        self._chunks.append(data)

    def get_text(self):
        return " ".join(self._chunks)


def _markdown_to_text(raw_markdown: str) -> str:
    extractor = _MarkdownTextExtractor()
    extractor.feed(markdown_parser.render(raw_markdown))
    extractor.close()
    return extractor.get_text()


def _sanitize_text(text: str) -> str:
    no_urls = URL_PATTERN.sub("", text)
    unescaped = unescape(no_urls)
    return WHITESPACE_PATTERN.sub(" ", unescaped).strip()

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
        submission.comments.replace_more(limit=0, threshold=2)
        # Use .list() to get flattened comment structure and slice to limit
        return list(submission.comments.list()[:limit])
    except Exception as e:
        print(f"Error fetching comments for post {submission.id}: {e}")
        return []

def clean_text(text):
    """Clean text by removing URLs, markdown formatting, and normalizing whitespace."""
    if not text:
        return ""

    plain_text = _markdown_to_text(text)
    return _sanitize_text(plain_text)

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
            'url': f"https://reddit.com{submission.permalink}",
            'flair': (getattr(submission, 'link_flair_text', '') or '').lower(),
            'len_text': len(post_text)
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
                    'flair': (getattr(submission, 'link_flair_text', '') or '').lower(),
                    'len_text': len(clean_comment_text)
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
    
    # Try to fetch 2 posts from given subreddit to validate credentials
    try:
        subreddit = reddit.subreddit("diy")
        test_posts = list(subreddit.hot(limit=2))  
        
        if test_posts:
            print("Reddit API authentication successful.")
        else:
            print("Reddit API authentication failed: No posts returned")
            return
            
    except Exception as e:
        print(f"Reddit API authentication failed: {e}")
        print("Unable to fetch posts from subreddit. Check your Reddit API credentials.")
        return
    
    # Fetch posts
    posts_list = fetch_posts(reddit, limit=5)
    
    # Build dataset
    dataset = build_dataset(posts_list, comment_limit=5)
    
    # Save to JSONL
    save_jsonl(dataset, filename="reddit_data.jsonl")
    
    print("Pipeline completed successfully!")

def main_small_run():
    """Fetch a small test dataset: 5 posts, 5 comments per post."""
    print("Starting small Reddit data pipeline...")
    
    posts_list = fetch_posts(reddit, limit=5)            # 5 posts
    dataset = build_dataset(posts_list, comment_limit=5) # 5 comments per post
    save_jsonl(dataset, filename="reddit_data_small.jsonl")
    
    print("Small dataset pipeline completed successfully!")


if __name__ == "__main__":
    #main()
    main_small_run()
