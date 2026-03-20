# LLM Execution Layer — Design Overview

## What This System Does
- Turns a validated `SummarizeRequest` into a validated `CurationResult`.
- Returns only ranked, relevant Reddit threads (no advice, no narrative summaries).
- Makes the output predictable, testable, and easy to render.

## Inputs and Outputs
- **Input:** `SummarizeRequest` (user query, evidence payloads, runtime limits, `prompt_version`).
- **Output:** `CurationResult` (`status`, `threads`, `limitations`, `prompt_version`).
- DTOs are the boundary contract: no extra fields, no missing required fields.

## Responsibilities
- Render prompt messages from `SummarizeRequest` and the selected `prompt_version`.
- Call the LLM with structured outputs and parse into `CurationResult`.
- Ensure threads are chosen only from the provided evidence set.
- Require short, evidence-focused `limitations` when results are thin or empty.

## Core Rules (What We Enforce)
- **Structure:** the model output must parse into `CurationResult`.
- **Evidence-only:** each thread must reference a `post_id` and `url` that exist in the input `post_payloads`.
- **Curation-only:** no advice, no step-by-step guidance, no quotes.
- **Ranking:** threads are ordered best-to-worst and have `rank` values 1..N.

## Prompt Versioning
- Prompts are versioned contracts that define the task and output shape.
- `prompt_version` in both request and result makes changes traceable and reviewable.

## Handling Weak Evidence
- If evidence is weak or loosely related: return fewer threads and set `status="partial"`.
- If nothing is clearly relevant: set `status="error"`, return an empty `threads` list, and provide a brief `limitations` reason.
- `limitations` must describe coverage/relevance/quality gaps (not “how-to” or instructions).

## Failure Modes
- **LLMTransportError:** provider/network/auth/rate-limit failures.
- **LLMStructuredOutputError:** output cannot be parsed into `CurationResult`.
- **ContractViolationError:** output parses but violates the curation contract (e.g., invented URLs).

## Non-Goals
- Not responsible for fetching, ranking, cleaning, or deduping evidence (done upstream).
- Not responsible for UI presentation or formatting decisions.
- Not responsible for infrastructure concerns (provider SDK details, deployments).

## Implementation Notes
- Uses the OpenAI Responses API with structured outputs.
- Current default model in configs: `gpt-4.1-mini`.
