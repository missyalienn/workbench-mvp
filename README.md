## 🧰 Workbench

**Workbench** is a research agent for DIY and home improvement projects built with OpenAI and Reddit APIs.  

Ask questions like:  
> “How do I hang floating shelves?”  
> “How do I unblock a shower drain?”  

- GPT takes the question and figures out which subreddits to search. 
- Workbench pulls in Reddit posts and comments, filters out the junk, and keeps the most helpful discussions.  
- Then it sends the results to GPT to summarize the best answers with links to the original posts, so you can check the sources. 

The DIY space can be overwhelming, with a hundred different ways to do one thing.  

Workbench cuts through the noise and surfaces relevant, community-sourced advice so you can do it yourself.  

---

## ⚙️ How It Works

OpenAI **gpt-4-mini** powers the **Planner**, which generates structured **Search Plans** (subreddits, search terms, and query intent).Search Plans are passed into a modular Reddit fetcher that manages data collection and validation.

**Data Pipeline:**
1. **Planner** generates Search Plans.  
2. **Reddit Client** handles OAuth, sessions, and raw Reddit API calls.  
3. **Fetcher** retrieves candidate posts and applies:
   - Hard metadata filters (no NSFW, ads, or invalid posts)
   - Text cleaning and normalization
   - Internal relevance scoring
   - Length checks and duplicate removal  
4. Posts that pass validation trigger **comment retrieval**:
   - Comments are filtered, scored, and modeled
   - A **Post** model is built with nested comments for full context  
5. The final validated dataset is exported as JSON for downstream LLM synthesis and evaluation.

---

### 🧱 Architecture Overview

- **Planner (`agent/planner/core/`)** – Generates structured Search Plans using gpt-4-mini.  
- **Reddit Client (`services/reddit_client/`)** – Manages Reddit OAuth (`RedditSession`), endpoints, and the `RedditClient` wrapper for HTTP requests.  
- **Fetcher (`services/fetch/`)** – Orchestrates post retrieval, filtering, comment pipelines, and builds structured `Post` and `Comment` models.  
- **Scoring & Filters (`services/fetch/content_filters/`, `services/fetch/comment_pipeline/`)** – Contain internal scoring logic, metadata checks, and quality filtering rules.  
- **Models (`models/`)** – Define the `Post` and `Comment` data schemas used throughout the pipeline.  
- **Scripts (`scripts/`)** – CLI tools for manual fetch previews, evaluations, and scoring.  
- **Docs**

---

## 🧱 Project Structure

- **`services/reddit_client/`** – Handles Reddit OAuth (`RedditSession`), raw API endpoints, and the high-level `RedditClient` for all HTTP calls.  
- **`services/fetch/`** – Core orchestrator layer with builders, validation helpers, and filtering logic that transforms raw Reddit payloads into structured `Post` and `Comment` models.  
- **`scripts/`** – CLI tools for fetch previews, evaluations, and manual scoring.  
- **`docs/`** – Architecture notes, evaluation summaries, and refactor plans.  

---

## 🧩 Current Capabilities

- Modular fetcher with isolated transport, validation, and builder layers.  
- CLI preview/eval scripts that output clean, structured datasets ready for LLM synthesis.  

---

## 🚧 Upcoming Work

- Unit tests for new helper modules (see inline TODOs).  
- Transport hardening (retries, rate limits) and a lightweight analyzer/synthesis demo aligned with the refactor plan.
