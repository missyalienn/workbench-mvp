# Reddit Fetcher Validation

## Upstream Reddit Validation (Veto Layer)
Hard-stop metadata checks run before any text processing. Each helper lives in `services/fetch/reddit_validation.py` so Reddit-specific rules stay isolated.

- `is_deleted_or_removed(raw_text)` → drops `[deleted]`, `[removed]`, or empty bodies for posts and comments.
- `is_auto_moderator(raw_item)` → rejects any submission/comment authored by `AutoModerator`.
- `is_created_from_ads_ui(raw_post)` → removes sponsored or promotional posts.
- `is_self_post(raw_post)` → enforces text-only submissions (`is_self == True`).
- `is_nsfw(raw_post)` → vetoes `over_18` content before downstream logic or comment fetches run.

## Cleaning Stage
`clean_text()` (in `fetch/utils/text_utils.py`) runs only after a record clears the veto layer. It strips Reddit markdown/HTML wrappers, collapses whitespace, and normalizes quotes/punctuation so length checks, scoring, and downstream summarizers all see consistent plain text.

## Relevance Scoring
After cleaning, `evaluate_post_relevance(title, body)` (from `fetch/scoring.py`) produces:
- `relevance_score` (float)
- `matched_keywords` (list[str])
- `passed_threshold` flag

This happens before quality filters so only posts that meet the semantic threshold proceed to comment fetching.

## Workbench Filters (Quality Layer)
Content-focused gates that run after cleaning + relevance scoring:

- `is_post_too_short(body)` / `is_comment_too_short(body)` enforce per-type minimum character counts.
- Dedupe sets (`seen_post_ids`, `seen_comment_ids`) prevent repeat submissions/comments within the same fetch run.

Only posts and comments that clear these filters are converted into `Post` and `Comment` models.

## Runtime Flow
```
fetch_posts (paginate_search with include_over_18=false, restrict_sr=1)
  → veto layer (deleted/removed, AutoModerator, ads, non-self, NSFW)
  → clean_text(title, selftext)
  → evaluate_post_relevance
  → quality filters (length, dedupe)
  → fetch_comments(post_id)
      → veto layer (deleted/removed, AutoModerator)
      → clean_text(comment body)
      → quality filters (length, dedupe)
      → build Comment models
  → build Post model (attach comments, permalink, scores)
→ aggregate into FetchResult (notes removed)
```

## Helper Function Locations

| Helper                              | Module                                     | Notes                                    |
|-------------------------------------|--------------------------------------------|------------------------------------------|
| `clean_text`                        | `fetch/utils/text_utils.py`                | Shared normalization utility             |
| `is_deleted_or_removed`             | `services/fetch/reddit_validation.py`      | Used by posts and comments               |
| `is_auto_moderator`                 | `services/fetch/reddit_validation.py`      | Rejects AutoModerator authors            |
| `is_created_from_ads_ui`            | `services/fetch/reddit_validation.py`      | Filters ad/promotional submissions       |
| `is_self_post`                      | `services/fetch/reddit_validation.py`      | Ensures text-only posts                  |
| `is_nsfw`                           | `services/fetch/reddit_validation.py`      | Post-level NSFW veto                     |
| `is_post_too_short` / `is_comment_too_short` | `services/fetch/reddit_fetcher.py`      | Post-cleaning quality checks             |
| Dedupe helpers / sets               | `services/fetch/reddit_fetcher.py`         | Maintained per run in orchestrator       |
| `evaluate_post_relevance`           | `fetch/scoring.py`                         | Semantic scoring before quality filters  |
| Transport helpers (`paginate_search`, `fetch_comments`) | `services/fetch/reddit_fetcher.py` | Handle `restrict_sr=1`, `include_over_18=false`, retries |

## Follow-up Notes
- If transport complexity grows, consider extracting HTTP/pagination helpers into a dedicated `reddit_transport.py` to keep validation/filtering modules pure.
- Keep `is_deleted_or_removed` content-agnostic so future sources (StackOverflow, etc.) can reuse it without Reddit-specific assumptions.
