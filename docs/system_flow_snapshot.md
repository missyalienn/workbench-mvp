# Workbench Reddit Assistant Flow (Snapshot)

## 1. User Asks a Question
- A user asks a DIY question inside Workbench (e.g., “How do I fix a leaky faucet?”).
- We capture the raw question and hand it to the agent stack.

## 2. Planner Creates a Search Plan
- `agent/planner/core.py` generates a `SearchPlan` using OpenAI.
- The plan includes:
  - `plan_id`: unique identifier for traceability.
  - `search_terms`: phrases to query Reddit (`["leaky faucet fix", "plumbing repair tips"]`).
  - `subreddits`: relevant communities (`["diy", "homeimprovement"]`).
  - `notes`: short reasoning about why those terms/subreddits were chosen.
- This plan is our blueprint for gathering instructional data.

## 3. Fetcher Pulls Reddit Data
- The fetcher (in progress) will:
  - Iterate through each `search_term` × `subreddit` pair.
  - Pull roughly 30 raw posts per plan and distribute requests round-robin across the subreddits so no single community dominates the sample.
  - Use `services/fetch/reddit_client.get_reddit_client()` to make REST requests while pacing calls under Reddit’s ~60-requests-per-minute guideline (add short sleeps or batching if needed).
  - Collect posts and their top-level comments (buffering 2–3× the target count for filtering).
  - Clean the text the same way we used to in the RAG pipeline (markdown → HTML → plain text).

## 4. Keyword Relevance Scoring
- Every candidate post runs through `services/fetch/scoring.evaluate_post_relevance()`:
  - Combine the title + body, lowercase it, and scan for keywords from `keyword_groups.py`.
  - Score increases when keywords from our positive groups appear (how-to, troubleshooting, etc.).
  - If no positive keywords matched, check for showcase/brag phrases.
  - Build a `relevance_score`, a list of matched positives, and any negative hits.
  - Compare the score to `MIN_POST_SCORE` (default 6.0) to decide if the post is worth keeping.
  - Log a structured message with the post ID, calculated score, matched keywords, and accept/reject reason.

## 5. Additional Filters (Planned)
- Outside the scoring helper we’ll run extra checks:
  - Drop NSFW posts.
  - Ensure body length and Reddit’s own `reddit_score` meet minimums.
  - De-duplicate posts by ID/title.
  - Fetch N top-level comments per post and clean them similarly.

## 6. Build FetchResult
- Accepted posts get packaged into `services/fetch/schemas.FetchResult`:
  - Carries the original plan info (`plan_id`, `search_terms`, `subreddits`, `notes`).
  - Top-level fields: `query`, `plan_id`, `search_terms`, `subreddits`, `notes`, `source`, `fetched_at`, `posts`.
  - Each `Post` carries `title`, `selftext`, `reddit_score`, `relevance_score`, `matched_keywords`, `url`, `comments`, `fetched_at`, `source`.
  - Comments track `id`, `body`, `score`, `source` (no relevance score yet).
  - Full schema lives in `services/fetch/schemas.py` if you need field-level details.
- FetchResult goes back to the agent pipeline for synthesis or downstream use.

## 7. Logging + Traceability
- Every scoring pass logs whether a post was accepted or rejected, along with a reason.
- Planner logs include plan IDs so fetch logs can reference the same context.
- This structure lets us audit decisions and quickly adjust keywords, weights, or thresholds.

## 8. Testing Outlook
- No automated tests yet. Short-term plan is to add script-based smoke checks in `scripts/` (e.g., hit `/api/v1/me`, fetch a few posts, run scoring) to sanity-check credentials and scoring outputs.
- Minimum unit tests once the fetcher lands:
  - `clean_text` normalization (markdown, links, emoji).
  - `evaluate_post_relevance` (positive vs. negative cases, weights, threshold).
  - Reddit client token caching (client-credential happy path, auth failure).
- After we wire the full fetch flow, add an integration smoke (pull one plan, produce a `FetchResult`) before expanding the test suite.
## Notes / Next Steps
- Move keyword groups & weights into YAML once tuning is done.
- Finalize the fetcher’s Reddit API loops and comment retrieval workflow.
- Add regression tests for `evaluate_post_relevance` and the cleaning utilities.
