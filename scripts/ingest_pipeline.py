
import json
import time
import re
from clients import get_reddit_client
from bs4 import BeautifulSoup
from markdown_it import MarkdownIt

# Initialize MarkdownIt instance
md = MarkdownIt()

#Initialize Reddit Client 
reddit= get_reddit_client()

ALLOWED_FLAIRS = {"help", "question", "advice", "how to"}
TITLE_KEYWORDS = ("how", "what", "why", "can", "should", "best way", "need help")

#Fetch posts 
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

#Fetch comments
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

#Clean Text
def clean_text(text):
    """Clean text by removing URLs, markdown formatting, and normalizing whitespace."""
    if not text:
        return ""
    
    # Convert Markdown to HTML first
    text = md.render(text)
    
    # Parse HTML with BeautifulSoup and extract text
    soup = BeautifulSoup(text, 'html.parser')
    text = soup.get_text(" ")
    
    # Remove URLs
    text = re.sub(r'https?://\S+', '', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

#Build Dataset
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
    #print(f"User Agent: {user_agent}")
    
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
    # Test clean_text() with sample Markdown strings
    print("🧪 Testing clean_text() with sample Markdown...")
    
    test_samples = [
        "This is **bold text** and *italic text* with a [link to Reddit](https://reddit.com)",
        "Here's a list:\n- Item 1\n- Item 2\n- Item 3\n\nAnd some `code` with ~~strikethrough~~",
        "Check out https://example.com and [another link](https://github.com) for more info"
    ]
    
    for i, sample in enumerate(test_samples, 1):
        cleaned = clean_text(sample)
        print(f"\n--- Test {i} ---")
        print(f"Input:  {sample}")
        print(f"Output: {cleaned}")
    
    print("\n✅ Clean text test complete!\n")
    
    # Uncomment below for Reddit pipeline test
    # #main()
    # #main_small_run()
    # print("🔧 Running quick Reddit + cleaning test...")
    # 
    # reddit = get_reddit_client()
    # print("✅ Reddit client authenticated:", reddit.read_only)
    # 
    # # Pick a subreddit and limit
    # subreddit = reddit.subreddit("diy")
    # posts = subreddit.top(time_filter="year", limit=10)
    # 
    # for post in posts:
    #     raw_text = f"{post.title}\n\n{post.selftext or ''}"
    #     cleaned_text = clean_text(raw_text)  # use your refactored cleaner here
    # 
    #     print("\n" + "=" * 80)
    #     print(f"Title: {post.title}")
    #     print(f"Flair: {post.link_flair_text}")
    #     print("\nRaw:\n", raw_text[:250], "..." if len(raw_text) > 250 else "")
    #     print("\nCleaned:\n", cleaned_text[:250], "..." if len(cleaned_text) > 250 else "")
    #     print("=" * 80)
    # 
    # print("\n✅ Test complete. No JSONL written.\n")  

