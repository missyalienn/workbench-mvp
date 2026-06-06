# Workbench

Workbench is an agentic research and due diligence system that converts an open-ended question into a structured retrieval workflow. Given a query, it generates a search plan, gathers relevant source material, ranks the results, and returns a structured research output with linked source results, summary context, relevance signals, and stated limitations.

The system is organized as a multi-stage application with distinct layers for planning, retrieval, result ranking, and structured response generation. The current production deployment exercises a scoped retrieval pipeline, while the broader architecture is designed to support additional sources and more flexible orchestration over time.

## What It Does

For each user query, Workbench:

1. Interprets the request and generates a search plan
2. Executes a retrieval pipeline against an external source
3. Scores, ranks, and normalizes the returned results
4. Returns a structured output containing:
   - search plan metadata
   - run status
   - a concise summary
   - ranked source results with direct links
   - selected source metadata, including engagement and relevance signals
   - explicit limitations

## Architecture

Workbench is organized into a small set of clear layers:

- `frontend/`
  - User-facing application for query submission and results display

- `api/`
  - Request handling, pipeline entrypoints, typed response models, and error boundaries

- `agent/`
  - Planning and orchestration logic that decomposes user requests into retrieval and response-generation steps

- `services/`
  - Retrieval clients, source normalization, ranking, and structured result generation

- `config/`
  - Runtime settings and deployment configuration

This separation keeps the application boundary, orchestration logic, source integration, and UI concerns isolated.

## Technical Focus

This project emphasizes:

- agentic workflow orchestration around LLM behavior
- typed interfaces between application layers
- retrieval, ranking, and structured result generation as separate responsibilities
- production-minded API, configuration, and deployment concerns
- testable backend services rather than notebook-style flows

## Current Production Scope

Workbench is designed with separable planning, retrieval, ranking, and response-generation layers. The current production deployment exercises one active retrieval pipeline and one frontend application surface.

That means the architecture is broader than the currently deployed scope. Today, the live system is centered on a single source-specific retrieval path, but it is structured so additional retrieval adapters and richer orchestration paths can be introduced without changing the overall product shape.

## Deployment

The current production deployment includes:

- a hosted frontend application
- a backend execution path for the retrieval workflow
- environment-aware runtime configuration for deployed execution
- structured API responses for downstream rendering

Recent production work focused on deployment configuration, async pipeline support, API hardening, and frontend integration for hosted use.

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 20+
- `uv` for Python dependency management

### Backend

```bash
uv sync
uv run uvicorn api.app:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Testing

```bash
uv run pytest
```

## Why This Project

Workbench is an exercise in building AI systems as software systems:

- turning ambiguous research questions into explicit workflow stages
- separating planning, retrieval, ranking, and response construction concerns
- enforcing application contracts around LLM-driven components
- moving from prototype workflows toward production deployment

## Status

Workbench is live in production in its current scoped form. Ongoing work is focused on expanding retrieval coverage, improving ranking quality, and adapting and hardening the system for both SMB and enterprise client use cases.
