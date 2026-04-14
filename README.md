## Workbench

**Workbench** is a research agent that takes a research task and returns grounded findings — ranked evidence from primary sources, structured limitations, and citations that let you verify claims directly.

The architecture is source-agnostic: the core pipeline is independent of any specific data source or domain. The current implementation uses Reddit as a data source applied to DIY and home improvement queries.

---

## How It Works

Workbench follows a structured evidence pipeline:

1. **Planner** generates a structured search plan from the user query.
2. **Evidence retrieval** gathers and validates candidate items from a data source.
3. **Semantic ranking** scores candidates by embedding similarity against the query; falls back to signal-based ordering on failure.
4. **Context building** selects top evidence and assembles an LLM-ready request with source attribution.
5. **LLM execution** returns structured evidence output with ranked sources and limitations.

---

## Output Contract

The system returns a structured **EvidenceResult**:
- `status`: research quality signal (`ok | partial | error`) — reflects evidence sufficiency, not system health
- `threads`: ranked evidence items with source URLs
- `limitations`: coverage or relevance caveats
- `prompt_version`: prompt template version used for this run

---

## Project Structure

- **`agent/planner/`** – Query planning logic and models.
- **`services/fetch/`** – Evidence collection, filtering, and validation.
- **`services/embedding/`** – Semantic ranking via OpenAI embeddings with SQLite cache.
- **`services/context_builder/`** – Evidence selection and LLM context assembly.
- **`services/synthesizer/`** – Prompt building, LLM execution, and output contracts.
- **`api/`** – FastAPI app and pipeline orchestration.
- **`frontend/`** – React demo UI.
- **`scripts/`** – CLI pipeline preview and eval tools.
- **`docs/`** – Architecture notes and design docs.

---

## Current Capabilities

- Modular evidence pipeline with isolated planning, retrieval, validation, and selection layers.
- Semantic ranking via embedding similarity with graceful fallback to signal-based ordering.
- Structured output contract with ranked sources and evidence quality signaling.
- FastAPI backend with a React frontend demo.

---

## Upcoming Work

- Multi-source evidence retrieval.
- Production-grade error handling at the API boundary.
- Embedding call batching to reduce per-request latency.
- Deployment preparation.
