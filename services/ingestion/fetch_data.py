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
def fetch_posts(reddit, limit=50):
    """Fetch up to `limit` posts from a subreddit with default search query and sorting."""
    logger.info("Fetching up to %d posts from r/%s.", limit, DEFAULT_SUBREDDIT)
    
    posts_list = []
    subreddit = reddit.subreddit(DEFAULT_SUBREDDIT)
    
    accepted_titles = []
    rejected_titles = []

    raw_limit = limit * 2
    logger.info("Searching up to %d raw posts to reach desired %d.", raw_limit, limit)

    for submission in subreddit.search(DEFAULT_SEARCH_QUERY, sort="new", limit=raw_limit):
        title = getattr(submission, "title", "").strip()
        post_id = getattr(submission, "id", "unknown")

        if include_post(submission):
            posts_list.append(submission)
            accepted_titles.append((post_id, title))
        else:
            rejected_titles.append((post_id, title))
        time.sleep(0.6)  # Respect Reddit API rate limits
        if len(posts_list) >= limit:
            break
    
    logger.info("Successfully fetched %d posts matching query.", len(posts_list))

    if accepted_titles:
        preview = "; ".join(f"{pid}: {title}" for pid, title in accepted_titles[:5])
        if len(accepted_titles) > 5:
            preview += "; ..."
        logger.info("Accepted posts (%d). Sample: %s", len(accepted_titles), preview)
    if rejected_titles:
        preview = "; ".join(f"{pid}: {title}" for pid, title in rejected_titles[:5])
        if len(rejected_titles) > 5:
            preview += "; ..."
        logger.info("Rejected posts (%d). Sample: %s", len(rejected_titles), preview)

    if rejected_titles:
        logger.info(
            "Post filter summary: accepted=%d, rejected=%d, desired=%d",
            len(accepted_titles),
            len(rejected_titles),
            limit,
        )

    return posts_list

# Fetch comments
def fetch_comments(submission, limit=4, min_score=1, min_words=8):
    """Fetch up to `limit` top-level comments that meet score/length thresholds."""
    submission.comment_sort = "top"
    try: 
        submission.comments.replace_more(limit=5, threshold=1)
    except Exception as exc:
        logger.error("replace more failed for post_%s:%s", submission.id, exc)
        return []

    comments = []
    kept = 0
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
            kept += 1

        if kept >= limit:
            break
    logger.info(
        "Fetched %d comments for post_%s (limit=%d)",
        kept,
        submission.id,
        limit,
    )
    if kept < 3:
        logger.warning(
            "Only %d qualifying comments for post_%s (min_score=%d, min_words=%d)",
            kept,
            submission.id,
            min_score,
            min_words,
        )
    return comments
