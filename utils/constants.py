import re 

#Default subreddit 
DEFAULT_SUBREDDIT = "diy"

#Allowed subreddit flairs for the default subreddit.
ALLOWED_FLAIRS = {"home improvement", "help", "other", "woodworking"}

#Title patterns for "instructional" post
TITLE_PATTERNS = re.compile(
    r"\b(how|what|why|where|can|should|best way|need|help|advice|fix|repair|install|problem)\b",
    re.I)

#Default search query 
DEFAULT_SEARCH_QUERY = "how OR fix OR repair OR help OR advice OR why OR can OR should"
