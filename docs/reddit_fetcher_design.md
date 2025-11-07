# RedditFetcher Design

## 1) Overview

RedditFetcher is the retrieval module that turns a Planner’s SearchPlan into structured Reddit content ready for LLM synthesis.

High‑level flow:
- Planner produces a SearchPlan (plan_id, subreddits, search_terms, notes).
- RedditFetcher queries Reddit, collects candidate posts, applies scoring + filters, then fetches top‑level comments.
- The result is a FetchResult with Post and Comment objects suitable for downstream summarization and planning.

Citation note:
- Every Post.url is a full Reddit permalink so the LLM can cite original sources in answers.

Where it fits:
Planner → Fetcher → Scoring/Filtering → FetchResult → Synthesis


## 2) Data Flow (existing models)

Inputs
- SearchPlan (agent/planner/model.py): plan_id, search_terms, subreddits, notes.

Outputs
- FetchResult (services/fetch/schemas.py): query, plan_id, search_terms, subreddits, notes, fetched_at, posts.
- Post: id, title, selftext, reddit_score, relevance_score, matched_keywords, url, comments, fetched_at, source.
- Comment: id, body, score, source.

LLM citation requirement
- The LLM needs a canonical source link for each item it uses. FetchResult exposes URLs via each Post.url (i.e., FetchResult.posts[*].url). The fetcher must always populate this field with the full Reddit permalink so answers can cite the source.

Processing steps (post-level):
1) For each subreddit × search_term, call Reddit search API (REST).
2) Clean title/body with clean_text before scoring.
3) Score with evaluate_post_relevance(title+body).
4) If passed: apply additional filters (NSFW, body length, dedupe).
5) If still accepted: fetch top‑level comments; clean and filter them.
6) Build Post objects and aggregate into FetchResult.


## 3) Two Layers: Transport vs Filtering

Why separate?
- Transport concerns (HTTP, auth, pagination, rate limits, retries) change independently from relevance and quality rules.
- Filtering logic is testable in isolation and reusable across sources.

Transport layer (I/O):
- Uses services/fetch/reddit_client.py for Session, OAuth token, and headers.
- Implements search pagination, rate‑limit handling, and simple retries with backoff.

Filtering layer (pure-ish logic):
- Normalizes text (clean_text) before any scoring or thresholds.
- Runs evaluate_post_relevance to get relevance_score and keyword matches.
- Applies NSFW, body‑length, and dedupe checks after relevance.
- Fetches and filters comments with the same normalization.


## 4) Key Helpers by Layer

Transport helpers (sync REST; no new types introduced):
- search_subreddit(...): Query `/r/{sub}/search` for a term with `restrict_sr=1`, handle `limit`, `after`, sort, and parse children → raw post dicts.
- paginate_search(...): Loop using `after` cursors to gather enough candidates, honoring rate limits.
- fetch_post_comments(...): Call `/comments/{id}` (or suitable endpoint) for top-level comments; return raw comment dicts.
- safe_request(...): Wrapper around Session.get with timeout, retry/backoff, and structured logging.

Filtering helpers (use existing schemas + utilities):
- preprocess_post(...): Extract and clean post title/selftext via clean_text.
- score_post(...): Call evaluate_post_relevance(post_id, title, body) and return relevance_score + matched_keywords.
- apply_post_filters(...): Enforce NSFW exclusion, minimum body length, and dedupe checks after scoring.
- normalize_key(...): Produce a stable dedupe key, e.g., lowercased, punctuation-stripped title.
- fetch_and_filter_comments(...): Given a post_id, call `/comments/{id}` for top-level replies, clean_text every body, enforce per-comment length/score/NSFW checks, log rejections, and return Comment models aligned to that post.
- build_post_model(...): Construct services/fetch/schemas.Post using cleaned content, reddit_score, relevance_score, matched_keywords, url, comments, fetched_at, source.

Notes
- Use clean_text for both posts and comments prior to any scoring/threshold decisions.
- Do not invent new fields; populate only those defined in services/fetch/schemas.py.


## 5) Logging and Retry

Logging (config/logging_config.py):
- API events: endpoint, params subset, status, duration.
- Pagination: page/after cursors, item counts.
- Filtering: for each rejection, log reason (nsfw, too_short, duplicate, below_threshold).
- Scoring: relevance_score, matched_keywords, threshold decision.
- Comment harvesting: log fetched vs accepted counts per post to tune thresholds and prove thread alignment.
- Errors: request failures, JSON decode, schema validation.

Retry basics:
- Use short exponential backoff with jitter for 5xx and 429 responses.
- Respect rate limiting hints (e.g., Retry‑After when present).
- Keep total retries modest; fail fast with clear error logs.
- All calls are synchronous requests; set a conservative timeout per call.


## 6) Post & Comment Filtering Rules

Order of operations (post):
1) Clean: title = clean_text(raw_title), body = clean_text(raw_selftext).
2) Score: relevance_score, matched_keywords = evaluate_post_relevance(...).
3) If failed threshold → reject (reason=below_threshold).
4) NSFW: reject if over_18 is true (reason=nsfw).
5) Body length: require a minimum non‑whitespace length or word count (reason=too_short).
6) Dedupe: reject if normalized title or id already seen (reason=duplicate).
7) Comments: fetch_and_filter_comments for accepted posts.

Order of operations (comment):
1) Fetch via `/comments/{post_id}` so replies are scoped to that post only (no cross-thread leakage).
2) Clean with clean_text.
3) Enforce minimum content length and optional NSFW/deleted checks; reject trivial replies.
4) Require a minimum Reddit score (e.g., ≥1) to keep community-endorsed answers.
5) Build Comment objects for survivors; attach them directly to the originating Post.


## 7) Pseudocode Sketch

"""
for subreddit in plan.subreddits:
    for term in plan.search_terms:
        for raw_post in paginate_search(subreddit, term):
            title = clean_text(raw_post.title)
            body  = clean_text(raw_post.selftext)

            score, positives, _, passed = evaluate_post_relevance(
                post_id=raw_post.id, title=title, body=body
            )
            if not passed:
                log(reject, reason="below_threshold")
                continue

            if raw_post.over_18:
                log(reject, reason="nsfw")
                continue

            if too_short(body):
                log(reject, reason="too_short")
                continue

            if is_duplicate(title, raw_post.id):
                log(reject, reason="duplicate")
                continue

            comments = fetch_and_filter_comments(raw_post.id)

            post = build_post_model(
                id=raw_post.id,
                title=title,
                selftext=body,
                reddit_score=raw_post.score,
                relevance_score=score,
                matched_keywords=positives,
                url=permalink(raw_post),
                comments=comments,
                fetched_at=now(),
            )
            result.posts.append(post)
"""


## 8) Extensibility

- Scoring: Swap or chain in semantic relevance without changing transport logic.
- Sources: Add more fetchers (e.g., StackExchange) that reuse filtering utilities.
- Comment depth: Extend to threaded comments later; keep current interface stable.
- Config: Externalize thresholds (length limits, retries) via settings/env.
- Telemetry: Add counters for acceptance/rejection reasons for tuning.


## 9) Testing Strategy

Unit tests (deterministic, no network):
- clean_text: markdown, links, whitespace, emoji removal.
- evaluate_post_relevance: sample inputs → expected pass/fail and matches.
- apply_post_filters: nsfw/body‑length/dedupe branches and logging of reasons.
- fetch_and_filter_comments: raw → cleaned, short comments removed.
- build_post_model: schema validation of required fields.

Integration tests (mocked HTTP with fixtures):
- search pagination (after cursors) and retry on transient errors.
- end‑to‑end: SearchPlan → FetchResult with consistent counts.

Notes:
- Mock requests.Session and reddit_client.get_reddit_client to avoid real network.
- Use fixed timestamps for fetched_at.
- Add assertions that every Post.url is non-empty and begins with "https://" to guarantee citation readiness.


## 10) Operational Defaults

- Synchronous requests only; small per‑request timeout.
- Conservative limits per subreddit/term to avoid rate issues.
- Log INFO summary and DEBUG details for local tuning.
- Fail fast on auth/secret errors with actionable messages.
