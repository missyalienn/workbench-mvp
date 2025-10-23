
import json
import time
import re
from bs4 import BeautifulSoup
from markdown_it import MarkdownIt

# Initialize MarkdownIt instance
md = MarkdownIt()

ALLOWED_FLAIRS = {"home improvement", "help", "other", "woodworking"}
TITLE_PATTERNS = re.compile(
    r"\b(how|what|why|where|can|should|best way|need|help|advice|fix|repair|install|problem)\b",
    re.I)

def include_post(submission) -> bool:
    """Keep only text-based instructional content."""
    
    flair = (getattr(submission, 'link_flair_text', '') or '').lower()
    #title = getattr(submission, "title", "") or ""
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
    """Fetch up to `limit` high-quality top-level comments from a submission."""
    submission.comment_sort = "top"
    submission.comments.replace_more(limit=5, threshold=1)

    comments = []
    for c in submission.comments:
        body = (getattr(c, "body", "") or "").strip()
        author = getattr(c, "author", None)
        name = getattr(author, "name", "").lower() if author else ""

        if (
            body
            and body not in ("[removed]", "[deleted]")
            and not getattr(c, "stickied", False)
            and "bot" not in name
            and name != "automoderator"
            and getattr(c, "score", 0) >= min_score
            and len(body.split()) >= min_words
        ):
            comments.append(c)

        if len(comments) >= limit:
            break

    print(f"Fetched {len(comments)} comments from post '{submission.title[:50]}...'")
    return comments

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
            comment_record = {
                'id': f"comment_{comment.id}",
                'type': 'comment',
                'text': clean_comment_text,
                'score': comment.score,
                'url': f"https://reddit.com{comment.permalink}",
                'link_id': f"post_{submission.id}",
                'flair': (getattr(submission, 'link_flair_text', '') or '').lower(),
                'len_text': len(clean_comment_text)
                }
            dataset.append(comment_record)
    
    print(f"Dataset created. Total: {len(dataset)} records")
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

