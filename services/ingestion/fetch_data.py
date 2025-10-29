import time
from utils.constants import (
    DEFAULT_SUBREDDIT, 
    DEFAULT_SEARCH_QUERY, 
)
from config.logging_config import get_logger
from .content_filters import include_post

# Initialize logger. 
logger = get_logger(__name__)

# Fetch posts 
def fetch_posts(reddit, limit=20):
    """Fetch up to `limit` posts from a subreddit with default search query and sorting."""
    logger.info("Fetching up to %d posts from r/%s.", limit, DEFAULT_SUBREDDIT)
    
    posts_list = []
    subreddit = reddit.subreddit(DEFAULT_SUBREDDIT)
    
    for submission in subreddit.search(DEFAULT_SEARCH_QUERY, sort="new", limit=limit):
        if include_post(submission): 
            posts_list.append(submission)
        time.sleep(0.6)  # Respect Reddit API rate limits
    
    logger.info("Successfully fetched %d posts matching query.", len(posts_list))
    return posts_list

# Fetch comments
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
