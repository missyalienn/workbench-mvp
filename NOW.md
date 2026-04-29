# NOW — workbench-mvp

## Current State
- V1 pipeline (planner → fetcher → ranking → context_builder → synthesizer) is working
- V2 LangGraph POC in progress on branch `feat/langgraph-poc`
- Package manager migrated from pip/requirements.txt to uv/pyproject.toml
- V2 scaffolding committed: prompts (scaffold), schemas, and state classes

## Last Decision
Expanded V2 scope from 4 to 5 due diligence dimensions — added `zoning` as its own agent/dimension alongside permits, violations, liens, and ownership.

## Next Steps
1. #127 — Tool protocol interfaces: `MunicipalDataClient`, `GeocodingClient`, `GeocodingResult` (`graph/tools/interfaces/municipal.py`)
2. #128 — Research and confirm NYC Open Data dataset IDs for all five dimensions
3. #129 — Research and confirm NYC Planning Geosearch API endpoint and response contract
