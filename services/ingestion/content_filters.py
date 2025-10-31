import re
from utils.constants import (
    ALLOWED_FLAIRS, 
    TITLE_PATTERNS,
)
from config.logging_config import get_logger

from bs4 import BeautifulSoup
from markdown_it import MarkdownIt

# Initialize logger 
logger = get_logger(__name__)

# Initialize Markdown instance
md = MarkdownIt()

# Include post if it meets the criteria (flair and keywords)
def include_post(submission) -> bool:
    """Define submission inclusion rules to ensure quality posts for dataset."""
    flair = (getattr(submission, 'link_flair_text', "") or '').lower()
    title = (getattr(submission, "title", "") or "").lower()
    body  = getattr(submission, "selftext", "") or ""
    post_id = getattr(submission, "id", "unknown")

    clean_body = clean_text(body)
    title_matches = TITLE_PATTERNS.search(title)

    if len(clean_body) < 20:
        if title_matches:
            logger.info(
                "Post retained despite short body (title informative): %s | %s",
                post_id,
                title,
            )
        else:
            logger.info(
                "Post filter failed (body too short + title mismatch): %s | %s",
                post_id,
                title,
            )
            return False

    if not title_matches:
        logger.info("Post filter failed (title mismatch): %s | %s", post_id, title)
        return False

    if flair and flair not in ALLOWED_FLAIRS:
        logger.info("Post filter failed (flair '%s' not allowed): %s | %s", flair, post_id, title)
        return False

    return True

# Clean Text
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
    # Remove emoji / non-ASCII characters
    text = re.sub(r'[^\x00-\x7F]+', '', text)

    return text
