
from .reddit_client import get_reddit_client
from .utils.text_utils import clean_text
from .scoring import evaluate_post_relevance
from .schemas import Post, Comment, FetchResult
from config.logging_config import get_logger

# -- Constants --
MIN_POST_LENGTH = 250
MIN_COMMENT_LENGTH = 140

logger = get_logger(__name__)

"""RedditFetcher pipeline contract (implementation TBD).

The fetcher turns a Planner-produced `SearchPlan` into a `FetchResult`
that downstream agents use to build a Guided Summary (curated links,
recurring themes, and a cautious action outline). Key stages:

1. Iterate each `(subreddit, search_term)` pair and call the Reddit
   search REST API via `services.fetch.reddit_client`.
   
   * Step 1: Define orchestator function that will call other helper functions.
   
   def run_reddit_fetcher(search_terms: list[str], subreddits: list[str], limit: int) -> FetchResult:
      pass
   

2. Normalize `title` and `selftext` with `text_utils.clean_text`
   before any scoring or dedupe so every downstream decision sees
   ASCII-safe content.

3. Run `scoring.evaluate_post_relevance(post_id, title, body)` to get
   `(relevance_score, positive_matches, negative_matches, passed)`.

4. Apply post-level filters only if `passed` is true:
   - NSFW: reject when `over_18` is true (we still send
     `include_over_18=false`, but local filtering is authoritative).
   - Body length: require minimum non-whitespace characters.
   - Dedupe: maintain a `seen_post_ids` set and drop duplicates; we do
     **not** dedupe on normalized titles so semantic variants survive.

5. For accepted posts, fetch top-level comments, run `clean_text` on
   each body, enforce comment-length/NSFW rules, and build
   standalone `Comment` models with `comment_id`, `post_id`,
   `body`, `comment_karma`, `fetched_at`, `source`.
   
   #TODO: fetch_and_filter_comments() function in reddit_fetcher.py
   #TODO: build_post_model() function in reddit_fetcher.py

6. Construct `schemas.Post` objects (fields include `post_karma`,
   `relevance_score`, `matched_keywords`, permalink URL, and the list
   of nested Comment models) plus FetchResult metadata
   (`plan_id`, `search_terms`, `subreddits`, `notes`, `fetched_at`,
   `source="reddit"`). Only approved posts/comments ever appear in the
   FetchResult.
   

# TODO: Create utc.now()helper in utils/datetime.py. Return timezone aware datetime (datetime.now(timezone.utc)).
# TODO: Define permalink function (reddit_fetcher.py)

7. Return the `FetchResult`; the summarizer prompt then:
   - Lists 3 to 5 curated Reddit links with short blurbs.
   - Highlights 2 to 4 recurring themes with citations.
   - Offers a cautious action outline synthesized from the cited posts
     while reminding users to verify details via the links.

Future enhancements (outside current scope):
- Persist standalone comments in a shared store/DB for analytics.
"""

def run_reddit_fetcher(search_terms: list[str], subreddits: list[str], limit: int) -> FetchResult:
   """
   Orchestator function that will call the other helper functions.
   """
   pass

# Helper Filtering Functions:
def is_nsfw(raw_post: dict) -> bool:
   """
   Check if the post is NSFW.
   """
   nsfw = bool(raw_post.get("over_18"))
   if nsfw:
    logger.info(f"Rejecting post {raw_post.get('id')}: NSFW")
   return nsfw


def is_post_too_short(body: str) -> bool:
   """
   Check if the post body is too short.
   """
   trimmed = body.strip()
   return len(trimmed) < MIN_POST_LENGTH

   # Dedupe logic (post-level):
   if post_id in seen_post_ids:
      logger.info("Rejecting post %s: duplicate", post_id)
      return True
   seen_post_ids.add(post_id)
   return False

# Comment Filtering Functions:
def fetch_and_filter_comments(post_id: str) -> list[Comment]:
   """
   Fetch and filter comments for a given post.
   - Fetch comments for a given post.
   - Clean the comments. (clean_text)
   -  
   - Return the filtered comments.
   """
   pass     

def is_comment_too_short(body: str) -> bool:
   """
   Check if the comment body is too short.
   """
   trimmed = body.strip()
   return len(trimmed) < MIN_COMMENT_LENGTH
