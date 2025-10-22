
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

ALLOWED_FLAIRS = {"home improvement", "help", "other", "woodworking"}
TITLE_PATTERNS = re.compile(
    r"\b(how|what|why|where|can|should|best way|need|help|advice|fix|repair|install|problem)\b",
    re.I)

def include_post(submission) -> bool:
    """Keep only text-based instructional content."""
    
    flair = (getattr(submission, 'link_flair_text', '') or '').lower()
    title = getattr(submission, "title", "") or ""
    body  = getattr(submission, "selftext", "") or ""

    # Require sufficient text content
    clean_body = clean_text(body)
    if len(clean_body) < 20:
        return False

    # Include if flair matches or title has instructional intent
    title_matches = bool(TITLE_PATTERNS.search(submission.title))
    return (flair in ALLOWED_FLAIRS) or title_matches or (flair == "" and title_matches)


#Fetch posts 
def fetch_posts(reddit, limit=20):
   
    print(f"Fetching up to {limit} post candidates from r/diy...")
    posts_list = []
    subreddit = reddit.subreddit("diy")
    
    query = "how OR fix OR repair OR help OR advice OR why OR can OR should"

    for i, submission in enumerate(subreddit.search(query, sort="new", limit=limit)):
        posts_list.append(submission)
        time.sleep(0.6)  # Respect Reddit API limits
    
    print(f"Successfully fetched {len(posts_list)} posts matching query.")
    return posts_list

#Fetch comments
def fetch_comments(submission, limit=20, min_score=3, min_words=15):
    """Fetch high-quality top-level comments for MVP efficiency."""
    try:
        submission.comment_sort = "top"
        submission.comments.replace_more(limit=5, threshold=1)
        
        comments = []
        for comment in submission.comments:
            body = getattr(comment, 'body', '').strip()
            words = body.split()
            
            if (body and comment.is_root and 
                body not in ['[removed]', '[deleted]'] and
                not getattr(comment, 'stickied', False) and
                comment.score >= min_score and len(words) >= min_words):
                comments.append(comment)
                if len(comments) >= limit:
                    break
        return comments
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
def build_dataset(posts_list, comment_limit=20):
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

def main_small_run():
    """Fetch a small test dataset: 5 posts, 5 comments per post."""
    print("Starting small Reddit data pipeline...")
    
    posts_list = fetch_posts(reddit, limit=5)            # 5 posts
    dataset = build_dataset(posts_list, comment_limit=5) # 5 comments per post
    #save_jsonl(dataset, filename="reddit_data_small.jsonl")
    print("Small dataset pipeline completed successfully!")

if __name__ == "__main__":
    start_time = time.time()
    reddit = get_reddit_client()
    #print("✅ Reddit client authenticated:", reddit.read_only)
    subreddit = reddit.subreddit("diy")
    posts = fetch_posts(reddit, limit=20)

    filtered_posts = [p for p in posts if include_post(p)]
    print(f"\n✅ Included {len(filtered_posts)}/{len(posts)} posts after filtering.\n")

    print("Included posts:\n")
    for p in filtered_posts:
        print(f"✅ {p.title} | Flair: {(p.link_flair_text or '').lower()}")
    print("\n---\nExcluded posts:\n")
    for p in posts:
        if p not in filtered_posts:
            print(f"❌ {p.title} | Flair: {(p.link_flair_text or '').lower()}")
    print(f"\n✅ Included {len(filtered_posts)} posts after filtering.\n")
    
    end_time = time.time()
    elapsed = end_time - start_time
    print(f"⏱️ Total runtime: {elapsed:.2f} seconds\n")
