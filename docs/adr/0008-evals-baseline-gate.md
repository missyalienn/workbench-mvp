# 0008 — Evals and baseline gate

**Status:** Accepted (2026-10-19)

**Context:** V2 has a different shape than V1, so V1 is not a meaningful comparison. Answer quality needs measurement; unit tests can't cover it.

**Decision:**
- LangSmith dataset (~25 representative DIY questions) scored with openevals LLM-as-judge: groundedness, answer relevance.
- Run manually (script / LangSmith pytest plugin); no CI.
- First accepted run = baseline. Prompt/model/retrieval changes must not regress below baseline minus tolerance.
- Unit tests cover all deterministic behavior; evals cover answer quality only.

**Consequences:**
- Cutover requires: accepted baseline, purge job (0007), hosting decided (0005), rate limiting (0006).
