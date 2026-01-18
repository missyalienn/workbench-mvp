# Minimal Demo UI for Workbench

## UI Layout (High Level)

### Header
- Workbench logo/name (text)
- Subtitle: "Agent-based research for DIY and home improvement. Ranked Reddit threads with source links."

### "How it works" blurb
- Workbench is an agent-based research tool. It designs search strategies, filters for quality, and returns ranked Reddit threads with source links. Built to surface signal, not noise.
- Positioned above the query box

### Query box
- One large text input
- Button: "See how others did it"
- Helper text: Examples like "Try: 'How do I hang floating shelves on drywall?'"

### Status / loading feedback
- Pipeline stage messages ("Planning search...", "Fetching posts...", "Analyzing evidence...")
- Error messages
- Rate-limit messages

### Search plan ("How we searched")
- Collapsible section, starts collapsed
- Subreddits searched
- Search terms used
- Reasoning

### Results
- Card per thread with:
  - Rank badge (#1, #2, etc) shown prominently
  - Subreddit badge (small pill)
  - Title (clickable to Reddit)
  - "View discussion on Reddit →" link
  - Relevance score is available in the API (ThreadEvidence.relevance_score) but intentionally not displayed in UI right now. 

### Limitations
- Warning-style (yellow/amber background)
- Lists coverage gaps from API response

### Footer
- "Built by [Your Name]"
- GitHub link

## Implementation Plan

### Scaffolding & folder structure
- Run: `npm create vite@latest frontend -- --template react-ts`
- See docs for Vite + Tailwind 3
- Structure:
```
frontend/src/
  App.tsx
  components/
    Header.tsx
    QueryBox.tsx
    LoadingState.tsx
    ResultsList.tsx
    SearchPlanPanel.tsx
    LimitationsBox.tsx
    Footer.tsx
  types/
    api.ts
  services/
    api.ts
```

---

### Types (API contracts)
- Create `frontend/src/types/api.ts`:
```typescript
export interface SearchPlan {
  search_terms: string[];
  subreddits: string[];
  notes?: string;
}

export interface ThreadEvidence {
  rank: number;
  post_id: string;
  title: string;
  subreddit: string;
  url: string;
  relevance_score: number;
}

export interface EvidenceResult {
  status: "ok" | "partial" | "error";
  threads: ThreadEvidence[];
  limitations: string[];
  prompt_version: string;
}

export interface DemoApiResponse {
  search_plan: SearchPlan;
  evidence_result: EvidenceResult;
}

export interface ApiError {
  type: "rate_limit" | "network" | "server" | "timeout";
  message: string;
}
```

---

### API integration
- Create `frontend/src/services/api.ts`:
  - Request payload: `{ query: string }`
  - POST to `http://localhost:8000/api/demo`
  - Timeout: 60s via `AbortController`
  - Handle: status `ok`/`partial`/`error`, HTTP 429 (rate limit), network failures, timeout
  - Export `submitDemoQuery(query: string)` and return `{ response?: DemoApiResponse, error?: ApiError }`

---

### Components (map to UI layout)
- `Header.tsx`: title "Workbench", subtitle "Agent-based research for DIY and home improvement. Ranked Reddit threads with source links."
- `QueryBox.tsx`: textarea, submit button, examples helper text below, "How it works" blurb above the query box
- `LoadingState.tsx`: stage messages ("Planning search...", "Fetching posts...", "Analyzing evidence...") + spinner
- `ResultsList.tsx`: cards with rank (large/prominent), subreddit pill, title link, "View discussion on Reddit →" link; empty state "No results found"; do not display relevance score (keep data available for future)
- `SearchPlanPanel.tsx`: collapsible panel titled "How we searched" (starts collapsed) showing subreddits list + search terms list + reasoning (label text "Reasoning", value from `notes`)
- `LimitationsBox.tsx`: only render if `limitations.length > 0`; amber background, list items
- `Footer.tsx`: "Built by [Your Name]" + GitHub link

---

### App wiring
- State: `query`, `loading`, `stageMessage`, `apiResponse`, `error`
- On submit: call API service, update loading/stage states, handle response/error
- Render: Header, QueryBox, conditional (LoadingState | Error | Results + SearchPlan + Limitations), Footer
- Acceptance: UI renders all states correctly, no TypeScript errors

---

### Test & acceptance
- Run backend: `uvicorn demo.app:app --reload` (port 8000)
- Run frontend: `cd frontend && npm run dev` (port 5173)
- Submit query "how to caulk bathtub", verify: loading stages display, results render, search plan expands, limitations show if present
- Acceptance: full request/response cycle works, no console errors

---

### Stop conditions
- All 7 components render without errors
- API integration handles all error types (rate limit, network, timeout, server) and displays appropriate messages
