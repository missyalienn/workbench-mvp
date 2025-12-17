# LLM Summarizer Design 

## Table of Contents
- [LLM Summarizer Design](#llm-summarizer-design)
  - [Table of Contents](#table-of-contents)
  - [Change Note — 2025-12-11](#change-note--2025-12-11)
  - [Overview](#overview)
  - [Goals and Non-Goals](#goals-and-non-goals)
    - [Goals](#goals)
    - [Non-Goals](#non-goals)
  - [Contracts and Schemas](#contracts-and-schemas)
    - [SummarizeRequest](#summarizerequest)
    - [PostPayload (Evidence Model)](#postpayload-evidence-model)
    - [SummarizeResult](#summarizeresult)
  - [Architecture and Components](#architecture-and-components)
    - [Configuration Structure (SelectorConfig and SummarizerConfig)](#configuration-structure-selectorconfig-and-summarizerconfig)
    - [Selector](#selector)
    - [Prompt Builder](#prompt-builder)
    - [LLM Client](#llm-client)
    - [Orchestrator](#orchestrator)
  - [Control Flow](#control-flow)
  - [Grounding, Safety, and Limits](#grounding-safety-and-limits)
    - [Rules to enforce](#rules-to-enforce)
    - [Limits](#limits)
  - [Observability and Evaluation](#observability-and-evaluation)
    - [Observability](#observability)
    - [Evaluation](#evaluation)
  - [Risks and Open Questions](#risks-and-open-questions)
    - [Potential risks](#potential-risks)
    - [Open questions](#open-questions)

## Change Note — 2025-12-11
Update `SummarizeResult` to support grounded, schema-constrained responses:
- Removed: `searched_subreddits`
- Added: `status`, `cautions`, `prompt_version`
- Added: `sources` `{post_id, HttpUrl url, subreddit, title}` (normalized citation list)

## Overview

Purpose: Take a `FetchResult` (curated Reddit posts + comments) and produce a brief, trustworthy research summary plus links to the original Reddit threads.

Scope: Help users understand common patterns, tradeoffs, and considerations around their DIY question, not give step-by-step repair instructions.

## Goals and Non-Goals

### Goals
- Provide a concise, grounded summary for a user query based on the fetched Reddit data.
- Always surface source links so users can read the underlying posts.
- Keep summarizer I/O stable and testable (explicit schemas and contracts).
- Make truncation and limits configurable (posts, comments, snippet lengths).

### Non-Goals
- Training custom models or implementing full RAG infrastructure.
- Providing detailed “how-to” or safety-critical instructions.
- Building a full UI; this phase focuses on a script/CLI and callable API.

## Contracts and Schemas

### SummarizeRequest

Input contract passed into the summarizer. Carries the user query, the selected evidence posts, and the runtime limits the summarizer must obey.

**Fields:**
- `query: str` — original user question.
- `plan_id: UUID` — traceability back to planner/fetcher runs.
- `post_payloads: list[PostPayload]` — trimmed list of posts/comments provided as evidence.
- `prompt_version: str` — identifies the prompt template used for this run.
- `max_posts: int` — cap applied by the selector when choosing posts.
- `max_comments_per_post: int` — per-post comment cap applied by the selector.
- `max_post_chars: int` — max characters kept in each post body excerpt.
- `max_comment_chars: int` — max characters kept in each comment excerpt.

**Additional summarizer limits (config-driven, injected at runtime):**
- `summary_char_budget: PositiveInt` — maximum allowed characters in the summary.
- `max_highlights: int` — maximum highlight items permitted.
- `max_cautions: int` — maximum caution items permitted.

**Comment count mental model:**
- `len(Post.comments)` = comments fetched and filtered by upstream logic.
- `len(PostPayload.top_comment_excerpts)` ≤ `max_comments_per_post` = comments actually shown to the LLM.
- `max_comments_per_post` = the cap recorded on the request.

---

### PostPayload (Evidence Model)

Compact representation of a Reddit post passed to the LLM. This is the *evidence set* the summarizer may cite.

**Fields:**
- `post_id: str`
- `subreddit: str` — normalized, lowercase.
- `title: str` — cleaned and truncated.
- `url: HttpUrl` — canonical Reddit permalink (tracking parameters removed).
- `body_excerpt: str` — truncated body text (≤ `max_post_chars`).
- `top_comment_excerpts: list[str]` — up to `max_comments_per_post` truncated comments (≤ `max_comment_chars`).
- `post_karma: int`
- `num_comments: int` — number of accepted comments for this post.
- `relevance_score: float`
- `matched_keywords: list[str]`

Upstream selector logic is responsible for de-duplication by `post_id`, excerpt cleaning, excerpt length enforcement, and comment ranking/truncation.

---

### SummarizeResult

Structured output returned by the summarizer. Enforces grounded, schema-constrained responses with validated citations.

**Fields:**
- `status: Literal["ok","partial","error"]` — summarization outcome for orchestrator logic.
- `summary: str` — concise primary narrative (adheres to `summary_char_budget`; may be truncated downstream).
- `highlights: list[str]` — ≤5 one-sentence takeaways derived from evidence.
- `cautions: list[str]` — ≤5 grounded risks, contradictions, or unknowns.
- `sources: list[dict]` — unique posts actually used in the summary. Each source includes:
  - `post_id: str`
  - `url: HttpUrl` — canonical Reddit permalink (validated against evidence)
  - `subreddit: str`
  - `title: str`  
  Notes: all URLs must come from the input evidence set; duplicates removed by `post_id`.
- `prompt_version: str` — identifier for the prompt variant used.

**Removed fields:**
- `ReferenceLink`
- `searched_subreddits`  
(Deprecated; replaced by normalized `sources[]` and upstream metadata.)

**Validation Notes:**
- All `sources[*].url` must appear in the input evidence set.
- Unknown or mismatched sources are dropped and `status="partial"`.
- Summarizer must not invent URLs or cite posts not present in the evidence.
- Output must be valid JSON matching this structure.

  - `prompt_version: str` – e.g., "v1", so we know which prompt template was used.
  - `max_posts: int` – cap applied when selecting posts.
  - `max_comments_per_post: int` – per-post comment cap applied while building payloads.
  - `max_post_chars: int` – max characters kept for each post body excerpt.
  - `max_comment_chars: int` – max characters kept for each comment excerpt.


## Architecture and Components

### Configuration Structure (SelectorConfig and SummarizerConfig)

To keep DTOs clean and preserve separation of concerns, configuration objects should live in component-specific config modules rather than in `models.py`.

- `SelectorConfig` should be moved to `services/selector/config.py`.
- `SummarizerConfig` should be created in `services/summarizer/config.py` and include:
  - `summary_char_budget`
  - `max_highlights`
  - `max_cautions`

These configs are read by the orchestrator and injected into `SummarizeRequest` at runtime.

### Selector
- Input: `FetchResult`.
- Output: `SummarizeRequest` context fields (list of `PostPayload` + limits).
- Responsibility: choose and compress the most relevant posts/comments (sort by relevance, trim text, pick top comment excerpts).

### Prompt Builder
- Input: `SummarizeRequest` + context.
- Output: final prompt text/messages.
- Responsibility: encode role, task, constraints, and context into a single template.

### LLM Client
- Input: prompt text/messages.
- Output: raw LLM response (string or structured).
- Responsibility: wrap the model provider API with basic error handling and retries.

### Orchestrator
- Entry point: `run_summarizer(fetch_result: FetchResult) -> SummarizeResult`.
- Responsibility: call selector → prompt builder → LLM client → parse to `SummarizeResult`, log metadata.

## Control Flow

Step-by-step narrative for running summarizer:
1. Accept `FetchResult` (in code or from a file)
2. Selector picks top posts/comments and builds `SummarizeRequest`
3. Prompt builder constructs the prompt using system instructions, query, and context
4. LLM client calls the model with the prompt
5. Orchestrator validates/parses the response into `SummarizeResult`, logs key metadata, and returns it

## Grounding, Safety, and Limits

### Rules to enforce
- No step-by-step DIY instructions or safety-critical guidance
- Model should only discuss posts present in the context
- Each major point should reference one or more Reddit URLs or IDs where possible
- If data is thin or low-quality, the summary should say so and encourage further research

### Limits
- Max posts, max comments per post, and max character lengths, all configurable

## Observability and Evaluation

### Observability
- What to log for each synthesis call (query, `plan_id`, number of posts, prompt version, etc.)
- Where logs will show up and how to correlate them with preview/eval JSONs

### Evaluation
- Small offline eval set: a handful of representative queries with saved `FetchResult` + `SummarizeResult`
- How to run synthesis on these cases and store sample outputs (e.g., `data/synthesis_previews/`)
- Simple qualitative checklist for reviewing summaries (grounded, honest, clear links)

## Risks and Open Questions

### Potential risks
- Hallucinations if prompts/context aren’t strict enough
- Summaries that feel too generic or too vague

### Open questions
- How aggressive truncation should be for v1
- Whether to move to more structured LLM output (e.g., JSON) in a later iteration
