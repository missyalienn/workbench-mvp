## LLM Summarizer Design – Workbench Reddit Agent

### 1. Overview

- **Purpose:** Take a `FetchResult` (curated Reddit posts + comments) and produce a brief, trustworthy research summary plus links to the original Reddit threads.
- **Scope:** Help users understand common patterns, tradeoffs, and considerations around their DIY question, not give step-by-step repair instructions.

### 2. Goals & Non-Goals

- **Goals**
  - Provide a concise, grounded summary for a user query based on the fetched Reddit data.
  - Always surface source links so users can read the underlying posts.
  - Keep synthesis I/O stable and testable (explicit schemas and contracts).
  - Make truncation and limits configurable (posts, comments, snippet lengths).

- **Non-Goals**
  - Training custom models or implementing full RAG infrastructure.
  - Providing detailed “how-to” or safety-critical instructions.
  - Building a full UI; this phase focuses on a script/CLI and callable API.

### 3. Contracts & Schemas (Summarizer)

**3.1 SummarizeRequest**

- Brief description of what this represents (input to the LLM layer).
- Fields (name, type, purpose), e.g.:
  - `query: str`
  - `plan_id: UUID`
  - `posts: list[PostContext]`
  - `prompt_version: str`
  - Config-driven limits (e.g., `max_posts`, `max_comments_per_post`).

**3.2 Context Models**

- How a post is represented in the synthesis layer (e.g., `PostContext`):
  - `title`, `url`, short `body_snippet`, optional stats (karma, comment count).
- Optional comment context model if needed (e.g., a small set of representative comments).
- Truncation rules and limits (how many posts/comments, max snippet length).

**3.3 SummarizeResult**

- Brief description of what this represents (output from the summarizer step).
- High-level shape (to be detailed later), e.g.:
  - Core fields for the user-facing summary and key points.
  - Source links back to Reddit posts.
  - Status/metadata fields to indicate success vs failure.

**3.4 Validation & Error Behavior**

- How we validate LLM output against `SynthesisResult`.
- What happens on parse/validation failure (e.g., safe fallback result + logged error).
- Any invariants (e.g., if `key_points` is non-empty, `sources` should contain at least one URL).

**3.5 Versioning & Extensibility**

- How we version the schema/prompt (e.g., `PROMPT_VERSION = "v1"`).
- Notes on adding new fields in a backward-compatible way.

### 4. Architecture & Components

- **Selector**
  - Input: `FetchResult`.
  - Output: `SynthesisRequest` context fields (e.g., list of `PostContext`).
  - Responsibility: choose and compress the most relevant posts/comments.

- **Prompt Builder**
  - Input: `SynthesisRequest` + context.
  - Output: final prompt text/messages.
  - Responsibility: encode role, task, constraints, and context into a single template.

- **LLM Client**
  - Input: prompt text/messages.
  - Output: raw LLM response (string or structured).
  - Responsibility: wrap the model provider API with basic error handling and retries.

- **Orchestrator**
  - Entry point: `run_synthesis(fetch_result: FetchResult) -> SynthesisResult`.
  - Responsibility: call selector → prompt builder → LLM client → parse to `SynthesisResult`, log metadata.

### 5. Control Flow

- Step-by-step narrative for `run_synthesis`:
  1. Accept `FetchResult` (in code or from a file).
  2. Selector picks top posts/comments and builds `SynthesisRequest`.
  3. Prompt builder constructs the prompt using system instructions + query + context.
  4. LLM client calls the model with the prompt.
  5. Orchestrator validates/parses the response into `SynthesisResult`, logs key metadata, and returns it.

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
  - Small offline eval set: a handful of representative queries with saved `FetchResult` + `SynthesisResult`.
  - How to run synthesis on these cases and store sample outputs (e.g., `data/synthesis_previews/`).
  - Simple qualitative checklist for reviewing summaries (grounded, honest, clear links).

### 8. Risks & Open Questions

- Potential risks:
  - Hallucinations if prompts/context aren’t strict enough.
  - Summaries that feel too generic or too vague.
- Open questions:
  - How aggressive truncation should be for v1.
  - Whether to move to more structured LLM output (e.g., JSON) in a later iteration.
