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
    
    return text
