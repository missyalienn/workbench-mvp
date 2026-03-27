# Rename Plan: `selector` → `context_builder` / `summarizer` → `synthesizer`

## Motivation

Two naming problems exist in the current service layer:

1. `services/selector/` contains only `SelectorConfig` (a data class), while the actual selection logic lives in `services/summarizer/selector.py`. The name "selector" appears in two unrelated places with no documented relationship.
2. `services/summarizer/` is a misnomer. The module does not summarize — it selects ranked posts, truncates them to fit token constraints, builds an LLM prompt, calls the model, and returns a structured `EvidenceResult`. The system's own design docs refer to this step as "curation."

These names will create friction as the system expands to multi-source pipelines and agentic workflows (v2+). Fixing them now, while the import surface is small, is lower cost than fixing them after further abstraction.

## Name Change Summary

| Old | New |
|---|---|
| `services/selector/` | `services/context_builder/` |
| `services/selector/config.py` | `services/context_builder/config.py` |
| `class SelectorConfig` | `class ContextBuilderConfig` |
| `services/summarizer/` | `services/synthesizer/` |
| `services/summarizer/selector.py` | `services/synthesizer/context_builder.py` |
| `services/summarizer/config.py` | `services/synthesizer/config.py` |
| `services/summarizer/models.py` | `services/synthesizer/models.py` |
| `services/summarizer/stage_summary.py` | `services/synthesizer/stage_summary.py` |
| `services/summarizer/llm_execution/` | `services/synthesizer/llm_execution/` |
| `build_summarize_request()` | `build_context_request()` |
| `_build_selector_config()` (pipeline helpers) | `_build_context_builder_config()` |
| `tests/services/selector/` | `tests/services/context_builder/` |
| `tests/services/selector/test_selector.py` | `tests/services/context_builder/test_context_builder.py` |

`EvidenceOutputConfig` and `_build_curator_config()` are already well-named — no changes.

---

## Resulting Pipeline

```
planner → fetcher → ranking → context_builder → synthesizer
```

Each name describes one transformation. None are tied to Reddit or the current single-source shape.

---

## Execution Order

```
Stage 1 → Stage 2 → Stage 3 → Stage 4 → Stage 5 → run tests → Stage 6
```

Do not update docs (Stage 6) until tests are green.

---

## Stage 1 — Rename `services/selector/` package

**Files touched:** `services/selector/config.py`, `services/selector/__init__.py`

1. Create `services/context_builder/` package with `__init__.py`
2. Move `config.py` into it; rename `SelectorConfig` → `ContextBuilderConfig`
3. Delete `services/selector/`

---

## Stage 2 — Rename and update `services/summarizer/selector.py`

**File:** `services/summarizer/selector.py` → `services/synthesizer/context_builder.py`

### Function renames

| Old | New |
|---|---|
| `build_summarize_request()` | `build_context_request()` |

`select_posts()`, `build_comment_excerpts()`, `build_post_payload()` are internal helpers — no rename needed.

### Import changes inside this file

```python
# old
from services.selector.config import SelectorConfig
from services.summarizer.config import EvidenceOutputConfig
from .models import PostPayload, EvidenceRequest

# new
from services.context_builder.config import ContextBuilderConfig
from services.synthesizer.config import EvidenceOutputConfig
from .models import PostPayload, EvidenceRequest
```

### Parameter type renames

All four function signatures use `cfg: SelectorConfig` — update to `cfg: ContextBuilderConfig`.

### Stale docstring

`build_context_request()` docstring currently says "SummarizeRequest DTO" — update to "EvidenceRequest" (matches the actual return type).

---

## Stage 3 — Rename `services/summarizer/` package to `services/synthesizer/`

### Files moved

| Old path | New path |
|---|---|
| `services/summarizer/__init__.py` | `services/synthesizer/__init__.py` |
| `services/summarizer/config.py` | `services/synthesizer/config.py` |
| `services/summarizer/models.py` | `services/synthesizer/models.py` |
| `services/summarizer/stage_summary.py` | `services/synthesizer/stage_summary.py` |
| `services/summarizer/llm_execution/__init__.py` | `services/synthesizer/llm_execution/__init__.py` |
| `services/summarizer/llm_execution/errors.py` | `services/synthesizer/llm_execution/errors.py` |
| `services/summarizer/llm_execution/llm_client.py` | `services/synthesizer/llm_execution/llm_client.py` |
| `services/summarizer/llm_execution/prompt_builder.py` | `services/synthesizer/llm_execution/prompt_builder.py` |
| `services/summarizer/llm_execution/types.py` | `services/synthesizer/llm_execution/types.py` |

### Internal import updates (path prefix only: `summarizer` → `synthesizer`)

- `services/synthesizer/llm_execution/prompt_builder.py` — `from services.summarizer.models` → `from services.synthesizer.models`
- `services/synthesizer/llm_execution/types.py` — same
- `services/synthesizer/llm_execution/llm_client.py` — same
- `services/synthesizer/stage_summary.py` — same

Delete `services/summarizer/` after all moves confirmed.

---

## Stage 4 — Update external callers

### `demo/pipeline.py`

**Imports (8 lines):**

```python
# old
from services.summarizer.config import EvidenceOutputConfig
from services.summarizer.llm_execution.llm_client import OpenAILLMClient
from services.summarizer.llm_execution.prompt_builder import build_messages
from services.summarizer.llm_execution.types import PromptMessage
from services.summarizer.models import EvidenceRequest, EvidenceResult
from services.summarizer.stage_summary import build_stage_diagnostics, ...
from services.summarizer.selector import build_summarize_request
from services.selector.config import SelectorConfig

# new
from services.synthesizer.config import EvidenceOutputConfig
from services.synthesizer.llm_execution.llm_client import OpenAILLMClient
from services.synthesizer.llm_execution.prompt_builder import build_messages
from services.synthesizer.llm_execution.types import PromptMessage
from services.synthesizer.models import EvidenceRequest, EvidenceResult
from services.synthesizer.stage_summary import build_stage_diagnostics, ...
from services.synthesizer.context_builder import build_context_request
from services.context_builder.config import ContextBuilderConfig
```

**Helper function renames:**
- `_build_selector_config()` → `_build_context_builder_config()`
- Return type annotation `SelectorConfig` → `ContextBuilderConfig`
- Call site: `build_summarize_request(...)` → `build_context_request(...)`

### `scripts/runs/run_evidence_preview.py`

Identical set of 8 imports and same two helper functions — apply the same changes as `demo/pipeline.py`.

### `scripts/runs/run_stage_summary.py`

One import:

```python
# old
from services.summarizer.stage_summary import build_stage_diagnostics, ...

# new
from services.synthesizer.stage_summary import build_stage_diagnostics, ...
```

---

## Stage 5 — Update tests

**Move:** `tests/services/selector/` → `tests/services/context_builder/`

**Rename:** `test_selector.py` → `test_context_builder.py`

**Import changes inside the test file:**

```python
# old
from services.selector.config import SelectorConfig
from services.summarizer.config import EvidenceOutputConfig
from services.summarizer.selector import build_comment_excerpts, ...

# new
from services.context_builder.config import ContextBuilderConfig
from services.synthesizer.config import EvidenceOutputConfig
from services.synthesizer.context_builder import build_comment_excerpts, ...
```

All references to `SelectorConfig` → `ContextBuilderConfig` throughout the test file (fixture factory, type annotations, inline usage).

---

## Stage 6 — Update docs

Update only after tests are green.

| File | What to update |
|---|---|
| `docs/design/llm_summarizer_design.md` | Rename `summarizer` → `synthesizer`; update module paths |
| `docs/notes/system_flow_snapshot.md` | Update pipeline stage names and module paths |
| `docs/design/semantic_ranking_design.md` | Update selector/summarizer path references |
| `docs/design/semantic_ranking_execution_plan.md` | Same |
| `docs/design/semantic_ranking_implementation.md` | Same |
| `docs/notes/manual_runs.md` | Update any module paths cited |
| `docs/design/reddit_fetcher_validation.md` | Update selector/summarizer path references |
| `docs/notes/scratch_repo_analysis.md` | Update repo map, component table, and pipeline flow diagram |

---

## Verification Checklist

Run after Stage 5, before Stage 6:

- [ ] `pytest tests/services/context_builder/` passes
- [ ] Full test suite passes
- [ ] `grep -r "services.summarizer" .` — zero hits outside `__pycache__`
- [ ] `grep -r "services.selector" .` — zero hits outside `__pycache__`
- [ ] `grep -r "SelectorConfig" .` — zero hits
- [ ] `grep -r "build_summarize_request" .` — zero hits
