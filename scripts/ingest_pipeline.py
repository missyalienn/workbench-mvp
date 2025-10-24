
import json
import time
import re
from bs4 import BeautifulSoup
from markdown_it import MarkdownIt
from utils.constants import (
    DEFAULT_SUBREDDIT, 
    DEFAULT_SEARCH_QUERY, 
    ALLOWED_FLAIRS, 
    TITLE_PATTERNS)
from config.logging_config import get_logger

logger = get_logger(__name__)

# Initialize MarkdownIt instance
md = MarkdownIt()

#Filters to keep only text-based instructional posts. 
def include_post(submission) -> bool:
    """Define submission inclusion rules to ensure quality posts for dataset"""
    flair = (getattr(submission, 'link_flair_text', "") or '').lower()
    title = (getattr(submission, "title", "") or "").lower()
    body  = getattr(submission, "selftext", "") or ""

    # Require sufficient text content
    clean_body = clean_text(body)
    if len(clean_body) < 20:
        logger.debug("Rejected: body too short (<20 chars)")
        return False
        
    title_matches = bool(TITLE_PATTERNS.search(title))
    return ((flair in ALLOWED_FLAIRS) and title_matches) or (flair == "" and title_matches)
    
#Fetch posts 
def fetch_posts(reddit, limit=20):
    """Fetch up to `limit` posts from a subreddit with default search query and sorting."""
    logger.info("Fetching up to %d posts from r/%s.", limit, DEFAULT_SUBREDDIT)
    
    posts_list = []
    subreddit = reddit.subreddit(DEFAULT_SUBREDDIT)
    
    for submission in subreddit.search(DEFAULT_SEARCH_QUERY, sort="new", limit=limit):
        posts_list.append(submission)
        time.sleep(0.6)  # Respect Reddit API rate limits
    
    logger.info("Successfully fetched %d posts matching query.", len(posts_list))
    return posts_list

#Fetch comments
def fetch_comments(submission, limit=20, min_score=3, min_words=15):
    """Fetch up to `limit` high-quality top-level comments from a submission."""
    submission.comment_sort = "top"
    try: 
        submission.comments.replace_more(limit=5, threshold=1)
    except Exception as exc:
        logger.error("replace more failed for post_%s:%s", submission.id, exc)
        return []

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
    logger.info(
        "Fetched %d comments for post_%s (limit=%d)",
        len(comments),
        submission.id,
        limit,
    )
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
    logger.info("Building dataset...")

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
    
    logger.info( "Dataset created. Total: %d records", len(dataset))

    return dataset

def save_jsonl(dataset, filename="reddit_data.jsonl", batch_size=100):
    """Save dataset to JSONL file in batches."""
    logger.info("Saving dataset to %s in batches of %d", filename, batch_size)
    
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
        
        logger.info(
            "Saved batch %d/%d (%d records)",
            i // batch_size + 1,
            (len(dataset) + batch_size - 1) // batch_size,
            len(batch),
        )
    logger.info("Dataset saved to %s. Total records: %d", filename, len(dataset))

