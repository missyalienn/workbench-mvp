import re 

#Default subreddit 
DEFAULT_SUBREDDIT = "diy"

#Allowed subreddit flairs for the default subreddit.
ALLOWED_FLAIRS = {
    "home improvement",
    "help",
    "other",
    "woodworking",
    "outdoor",
    "tools",
}

#Title patterns for "instructional" post
TITLE_PATTERNS = re.compile(
    r"\b("
    r"how|what|why|where|when|who|is|are|do|does|did|can|should|would|could|"
    r"best way|need|help|advice|fix|repair|install|replace|prevent|maintain|"
    r"tools|materials|supplies|tips|ideas|guide|process|plan|cost|budget|"
    r"approach|method|safely|safety|basement|suggestions|missing|looking|"
    r"dishwasher|window|closet|damage|repair|restore|refinish|refurbish|replace"
    r")\b",
    re.I
)

#Default search query 
DEFAULT_SEARCH_QUERY = "how OR fix OR repair OR help OR advice OR why OR can OR should"
