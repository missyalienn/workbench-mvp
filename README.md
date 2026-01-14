## Workbench

**Workbench** is a research agent that performs evidence retrieval, selection, and grounding for a user query.

This repo currently applies the system to DIY and home improvement, but the same architecture can be adapted to enterprise knowledge bases or other domains by swapping data sources.

---

## How It Works

Workbench follows a structured evidence pipeline that keeps the core use case independent of any specific data source or framework.

**Evidence Pipeline:**
1. **Planner** generates a structured search plan from the user query.  
2. **Evidence retrieval** gathers candidate items from one or more sources.  
3. **Validation + scoring** filters, normalizes, and ranks evidence.  
4. **Evidence selection + grounding** builds an LLM-ready request with source attribution.  
5. The **LLM execution layer** returns structured evidence output with ranked sources and limitations.

---

### Architecture Overview

- **Planner** – Produces structured search plans from a query.  
- **Evidence retrieval** – Collects candidate items from source-specific adapters.  
- **Validation + scoring** – Applies quality rules, deduping, and relevance scoring.  
- **Evidence selection + grounding** – Builds an LLM-ready request with source attribution.  
- **LLM execution** – Produces a structured, grounded evidence result.  
- **Models** – Data contracts used across the pipeline.  
- **Scripts** – CLI tools for smoke tests and preview runs.  
- **Docs** – Architecture notes and refactor plans.

---

## DIY/Home Improvement Application

Example user queries:  
> “How do I hang floating shelves?”  
> “How do I unblock a shower drain?”

Current implementation details:
- Data source: Reddit  
- Planner: OpenAI Completions  
- Grounded evidence output: OpenAI Responses API

The DIY space can be overwhelming, with a hundred different ways to do one thing.

Workbench cuts through the noise and surfaces relevant, community-sourced evidence so you can check sources directly.

---

## Output Contract

The system returns a structured **EvidenceResult** (name pending) with:
- `status`: ok | partial | error
- `threads`: ranked evidence items with source URLs/IDs
- `limitations`: brief coverage or relevance caveats
- `prompt_version`: request/contract version

---

## Project Structure

- **`services/fetch/`** – Evidence collection, filtering, validation, and scoring logic.  
- **`services/summarizer/`** – Selection, prompt building, LLM execution, and structured output contracts.  
- **`agent/planner/`** – Query planning logic and models.  
- **`scripts/`** – CLI smoke test and preview tools.  
- **`docs/`** – Architecture notes and refactor plans.

---

## Current Capabilities

- Modular evidence pipeline with isolated planning, retrieval, validation, and selection layers.  
- LLM execution layer that returns structured evidence output with source attribution.  
- CLI smoke test that writes preview JSON artifacts for inspection.

---

## Upcoming Work

- Dependency inversion + explicit use-case boundary for the end-to-end flow.  
- Unit and integration tests  
- Streamlit demo layer
