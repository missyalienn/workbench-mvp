# RedditFetcher System Design

## Overview

**RedditFetcher** is designed to retrieve high-quality, instructional Reddit posts and top-level comments for Workbench, supporting the automatic generation of helpful DIY plans. The system prioritizes posts and discussions that are educational, question-focused, or genuinely step-by-step, enabling downstream models to generate actionable, beginner-friendly responses.

---

## Architecture & Design Principles

- **Standalone & Modular:** RedditFetcher is architected as its own service, agnostic to ingestion or legacy pipelines.
- **Instructional Focus:** Prioritizes posts that are clearly how-to, tutorial, or question/answer oriented.
- **Pragmatic Filtering:** Uses a fast, tuneable keyword scoring approach for post relevance in v1 (semantic embeddings may be added in later versions).
- **No Flair Filtering:** Allows flexible support for diverse subreddits and post types without hardcoded flair logic.
- **Flat Comment Retrieval:** Retrieves only top-level comments per post (no threads) to keep logic simple and consistent.
- **Comprehensive Metadata:** Captures Reddit post URLs for easy citation and downstream referencing.

---
## Data Retrieval and Filtering Workflow

### 1. Post Collection

* Accepts `subreddits` and `search_terms` from the **SearchPlan**.
* Queries each subreddit for **top** or **recent** posts matching the provided terms.
* Retrieves approximately **2–3×** the target result count to support downstream filtering.
* Performs **no flair-based filtering or sorting** during retrieval.

### 2. Keyword-Based Post Scoring

* Each post is scored using a weighted list of instructional/question keywords (e.g., "how do I", "step by step", "help", "tutorial").
* Keyword weights are summed across the cleaned title and body text, then normalized to a 0–1 range for consistency.
* Showcase phrases act as a hard veto only when no positive instructional keywords appear; posts with both signals fall back to scoring rather than automatic exclusion.
* Keyword matching expands each root term with simple suffix variants (e.g., "dent", "dented", "denting") so the config stays small while covering common phrasing.
* Posts must exceed a configurable minimum keyword relevance score to be included.
* Additional filters: minimum upvote count, body/content length, and exclusion of removed/deleted/NSFW posts.
* Scoring and filtering run **after text cleaning** for consistent tokenization.

---

### 3. Duplicates & Noise Handling

* Dedupe by normalized title or Reddit post ID.
* Exclude non-instructional "showcase" or brag posts by identifying common patterns in title/content (e.g., "look what I built").
* Document and log filtered results for analysis, including counts of excluded posts and their reasons (e.g., duplicate, low score, NSFW).
* Handle Reddit API rate limits and request errors using short exponential backoff and retry logic.

---

### 4. Flat Comment Retrieval

* For each qualifying post, fetch **N** top-level comments (by upvotes, minimum word count).
* No retrieval of comment threads or children yet; only direct replies to the submission.
* Clean comment text using the same normalization applied to posts.
* Log comment counts and filter stats to monitor over-aggressive pruning.

---

### 5. Output Format

* Aggregate qualified posts and comments into a structured **FetchResult** object for downstream synthesis.
* Include planner metadata (`plan_id`, `search_terms`, `notes`) and retrieval metadata (`source`, `fetched_at`).
* Ensure all posts retain their original Reddit URLs to enable citations in model outputs.
* The final FetchResult is JSON-serializable and ready for immediate use by the synthesis layer.

---

##  Schema Design 

### Post Schema 
| Field        | Type            | Description                                                     |
| ------------ | --------------- | --------------------------------------------------------------- |
| `id`         | `str`           | Reddit post ID (`t3_...`).                                      |
| `title`      | `str`           | Cleaned post title.                                             |
| `selftext`   | `str`           | Cleaned body text of the post.                                  |
| `score`      | `int`           | Reddit score (upvotes − downvotes).                             |
| `url`        | `str`           | Full Reddit permalink (absolute URL).                           |
| `comments`   | `list[Comment]` | List of top-level comments meeting quality thresholds.          |
| `fetched_at` | `float`         | Timestamp of when this post was retrieved.                      |
| `source`     | `str`           | Always `"reddit"` for now (future-proof for multiple fetchers). |

---

### Comment Schema 

| Field    | Type  | Description                     |
| -------- | ----- | ------------------------------- |
| `id`     | `str` | Reddit comment ID (`t1_...`).   |
| `body`   | `str` | Cleaned comment text.           |
| `score`  | `int` | Comment score (quality signal). |
| `source` | `str` | `"reddit"`.                     |

---

### FetchResult Schema

| Field          | Type         | Description                                                           |
| -------------- | ------------ | --------------------------------------------------------------------- |
| `plan_id`      | `str`        | Unique identifier for the originating SearchPlan.                     |
| `search_terms` | `list[str]`  | Terms used to query Reddit.                                           |
| `subreddits`   | `list[str]`  | Subreddits targeted by the Planner.                                   |
| `notes`        | `str`        | Planner reasoning or notes explaining the search strategy.            |
| `source`       | `str`        | Origin of the data (e.g., `"reddit"`).                                |
| `fetched_at`   | `float`      | UTC timestamp of when the fetch occurred.                             |
| `posts`        | `list[Post]` | List of structured Reddit posts and comments retrieved for synthesis. |


## Goals & Future Directions

- **Demo-Ready:** Minimal, robust, and fast for solo development.
- **Instructional Relevance:** Ensures model input is dense with actionable, question-driven content.
- **Future-Proofing:** The design is modular; future versions may add semantic filtering (embeddings), comment threading, or advanced summarization.

---

This design keeps RedditFetcher lightweight while ensuring retrieval quality and downstream compatibility for instructional content synthesis.

## Key workstreams and dependencies

- Accept SearchPlan inputs (plan id, subreddits, search terms, notes) and drive subreddit queries for both recent/top posts; depends on an injected Reddit API client plus clock and config providers.
- Clean and normalize titles/bodies/comments before scoring; needs shared text utilities and configurable keyword weight table, min scores, minimum post/comment thresholds.
- Score posts via weighted keyword matcher, filter by score/upvotes/content length/NSFW flags, and track filter reasons; requires scoring config, logging/metrics sink, and rate-limit-aware retry helper.
- De-duplicate qualifying posts by normalized title or post id, then fetch top-level comments meeting thresholds via same API client.
- Assemble structured FetchResult with metadata, post/comment models, timestamps, logging for inclusion/exclusion counts; relies on serialization helpers and schema definitions.


