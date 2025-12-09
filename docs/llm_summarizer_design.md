## LLM Summarizer Design – Workbench Reddit Agent

### 1. Overview

- **Purpose:** Take a `FetchResult` (curated Reddit posts + comments) and produce a brief, trustworthy research summary plus links to the original Reddit threads.
- **Scope:** Help users understand common patterns, tradeoffs, and considerations around their DIY question, not give step-by-step repair instructions.

### 2. Goals & Non-Goals

- **Goals**
  - Provide a concise, grounded summary for a user query based on the fetched Reddit data.
  - Always surface source links so users can read the underlying posts.
  - Keep summarizer I/O stable and testable (explicit schemas and contracts).
  - Make truncation and limits configurable (posts, comments, snippet lengths).

- **Non-Goals**
  - Training custom models or implementing full RAG infrastructure.
  - Providing detailed “how-to” or safety-critical instructions.
  - Building a full UI; this phase focuses on a script/CLI and callable API.

### 3. Contracts & Schemas (Summarizer)

**3.1 SummarizeRequest**

- Input contract passed into the summarizer/LLM layer.
- Fields (all required unless noted):
  - `query: str` – original user question.
  - `plan_id: UUID` – traceability back to planner/fetcher runs.
  - `post_payloads: list[PostPayload]` – trimmed list of posts/comments we will show the LLM.
  - `prompt_version: str` – e.g., "v1", so we know which prompt template was used.
  - `max_posts: int` – cap applied when selecting posts.
  - `max_comments_per_post: int` – per-post comment cap applied while building payloads.
  - `max_post_chars: int` – max characters kept for each post body excerpt.
  - `max_comment_chars: int` – max characters kept for each comment excerpt.

**Comment count mental model**

- `len(Post.comments)` inside `FetchResult` – comments we fetched + accepted after filters.
- `len(PostPayload.top_comment_excerpts)` ≤ `max_comments_per_post` – comments actually passed to the LLM.
- `max_comments_per_post` – the configurable cap recorded on the request.

**3.2 Context Models (PostPayload)**

- Compact representation of a Reddit post handed to the LLM:
  - `post_id: str`
  - `subreddit: str`
  - `title: str`
  - `url: str`
  - `body_excerpt: str` – truncated body text (≤ `max_post_chars`).
  - `top_comment_excerpts: list[str]` – up to `max_comments_per_post` truncated comment bodies (≤ `max_comment_chars`).
  - `post_karma: int`
  - `num_comments: int` – number of comments accepted by the fetcher for this post.
  - `relevance_score: float` – scorer output from the fetcher.
  - `matched_keywords: list[str]` – keywords that triggered this post.

- Selector logic (see Section 4) is responsible for sorting comments (e.g., by karma), taking the top N, truncating, and populating `top_comment_excerpts`.

**3.3 SummarizeResult**

- Output contract returned by the summarizer/LLM layer.
- Fields:
  - `searched_subreddits: list[str]` – subreddits the planner/fetcher consulted for this run.
  - `summary: str` – main narrative answer distilled from the context.
  - `highlights: list[str]` – optional bullet points or key takeaways.
  - `reference_links: list[ReferenceLink]` – citations pointing back to supporting posts.
- `ReferenceLink` helper:
  - `label: str` – human-friendly title for the reference.
  - `url: str` – canonical link the user can follow.
  - `subreddit: str | None` – subreddit name tied to this reference, if known.
  - `post_id: str | None` – Reddit post identifier for cross-linking with `PostPayload`.
- Quick REPL sanity check:
  ```python
  from services.summarizer.models import ReferenceLink, SummarizeResult

  reference = ReferenceLink(
      label="DIY wiring tips",
      url="https://reddit.com/r/diy/comments/abc123/help/",
      subreddit="diy",
  )

  result = SummarizeResult(
      searched_subreddits=["diy", "homeimprovement"],
      summary="Turn off power, label wires, and verify connections before rewiring.",
      highlights=["Kill power at the breaker", "Use labels to track wires"],
      reference_links=[reference],
  )

  print(result.model_dump())
  ```

**3.4 Validation & Error Behavior**

- How we validate LLM output against `SummarizeResult`.
- What happens on parse/validation failure (e.g., safe fallback result + logged error).
- Any invariants (e.g., if `key_points` is non-empty, `sources` should contain at least one URL).

**3.5 Versioning & Extensibility**

- How we version the schema/prompt (e.g., `PROMPT_VERSION = "v1"`).
- Notes on adding new fields in a backward-compatible way.

### 4. Architecture & Components

- **Selector**
  - Input: `FetchResult`.
  - Output: `SummarizeRequest` context fields (list of `PostPayload` + limits).
  - Responsibility: choose and compress the most relevant posts/comments (sort by relevance, trim text, pick top comment excerpts).

- **Prompt Builder**
  - Input: `SummarizeRequest` + context.
  - Output: final prompt text/messages.
  - Responsibility: encode role, task, constraints, and context into a single template.

- **LLM Client**
  - Input: prompt text/messages.
  - Output: raw LLM response (string or structured).
  - Responsibility: wrap the model provider API with basic error handling and retries.

- **Orchestrator**
  - Entry point: `run_summarizer(fetch_result: FetchResult) -> SummarizeResult`.
  - Responsibility: call selector → prompt builder → LLM client → parse to `SummarizeResult`, log metadata.

### 5. Control Flow

- Step-by-step narrative for `run_summarizer`:
  1. Accept `FetchResult` (in code or from a file).
  2. Selector picks top posts/comments and builds `SummarizeRequest`.
  3. Prompt builder constructs the prompt using system instructions + query + context.
  4. LLM client calls the model with the prompt.
  5. Orchestrator validates/parses the response into `SummarizeResult`, logs key metadata, and returns it.

### 6. Grounding, Safety & Limits

- Rules to enforce:
  - No step-by-step DIY instructions or safety-critical guidance.
  - Model should only discuss posts present in the context.
  - Each major point should reference one or more Reddit URLs or IDs where possible.
  - If data is thin or low-quality, the summary should say so and encourage further research.
- Limits:
  - Max posts, max comments per post, and max character lengths, all configurable.

### 7. Observability & Evaluation

- **Observability**
  - What to log for each synthesis call (query, `plan_id`, number of posts, prompt version, etc.).
  - Where logs will show up and how to correlate them with preview/eval JSONs.

- **Evaluation**
  - Small offline eval set: a handful of representative queries with saved `FetchResult` + `SummarizeResult`.
  - How to run synthesis on these cases and store sample outputs (e.g., `data/synthesis_previews/`).
  - Simple qualitative checklist for reviewing summaries (grounded, honest, clear links).

### 8. Risks & Open Questions

- Potential risks:
  - Hallucinations if prompts/context aren’t strict enough.
  - Summaries that feel too generic or too vague.
- Open questions:
  - How aggressive truncation should be for v1.
  - Whether to move to more structured LLM output (e.g., JSON) in a later iteration.
