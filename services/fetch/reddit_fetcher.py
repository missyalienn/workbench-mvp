"""RedditFetcher pipeline contract (implementation TBD).

The fetcher turns a Planner-produced `SearchPlan` into a `FetchResult`
that downstream agents use to build a Guided Summary (curated links,
recurring themes, and a cautious action outline). Key stages:

1. Iterate each `(subreddit, search_term)` pair and call the Reddit
   search REST API via `services.fetch.reddit_client`.
2. Normalize `title` and `selftext` with `text_utils.clean_text`
   before any scoring or dedupe so every downstream decision sees
   ASCII-safe content.
3. Run `scoring.evaluate_post_relevance(post_id, title, body)` to get
   `(relevance_score, positive_matches, negative_matches, passed)`.
4. Apply post-level filters only if `passed` is true:
   - NSFW: reject when `over_18` is true (we still send
     `include_over_18=false`, but local filtering is authoritative).
   - Body length: require minimum non-whitespace characters.
   - Karma: require minimum native Reddit karma.
   - Dedupe: maintain a `seen_post_ids` set and drop duplicates; we do
     **not** dedupe on normalized titles so semantic variants survive.
5. For accepted posts, fetch top-level comments, run `clean_text` on
   each body, enforce comment-length/karma/NSFW rules, and build
   standalone `Comment` models with `comment_id`, `post_id`,
   `body`, `comment_karma`, `fetched_at`, `source`.
6. Construct `schemas.Post` objects (fields include `post_karma`,
   `relevance_score`, `matched_keywords`, permalink URL, and the list
   of nested Comment models) plus FetchResult metadata
   (`plan_id`, `search_terms`, `subreddits`, `notes`, `fetched_at`,
   `source="reddit"`). Only approved posts/comments ever appear in the
   FetchResult.
7. Return the `FetchResult`; the summarizer prompt then:
   - Lists 3–5 curated Reddit links with short blurbs.
   - Highlights 2–4 recurring themes with citations.
   - Offers a cautious action outline synthesized from the cited posts
     while reminding users to verify details via the links.

Future enhancements (outside current scope):
- Persist standalone comments in a shared store/DB for analytics.
- Push curated links/themes/action outline into a user notebook to
  reduce manual curation.
"""
