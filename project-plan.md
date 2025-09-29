# Implementation Plan

## Workbench - Your DIY Project Companion 

**Goal**: Functional MVP with core features


## Phase 1: Reddit Auth & Data Pipeline

### Task 1.1: Environment Setup
- [ ] Initialize project structure per `agents.md` rules
- [ ] Create `.env` and `.gitignore` (exclude `.env`)
- [ ] Create `requirements.txt` with core dependencies

### Task 1.2: Reddit Data Ingestion
- [ ] Authenticate to Reddit API  
- [ ] Fetch top N posts and top M comments from `r/diy` (configurable)  
- [ ] Store raw data in JSON  
- [ ] Clean/normalize text (remove markdown, URLs, whitespace)

### Task 1.3: Vectorization
- [ ] Generate embeddings with Sentence Transformers  
- [ ] Set up Pinecone client (or local vector store for MVP)  
- [ ] Upload sample vectors and test retrieval with sample data

**Deliverable**: Minimal working data pipeline with searchable vectors

---

## Phase 2: Search API & RAG System

### Task 2.1: Search Service
- [ ] Implenent core semantic search module
- [ ] Query preprocessing and ranking
- [ ] Return top resutls with minimal metadata

### Task 2.2: RAG Response System
- [ ] Format search results for display
- [ ] Include source references with formatting
- [ ] Response structure design
- [ ] Basic error handling
- [ ] Performance optimization

**Deliverables**: Working RAG system with semantic search that can return and format search results. 

---

## Phase 3: CLI & Optional LLM Integration

### Step 3.1: CLI Interface
- [ ] Simple command-line interface for question input and response display
- [ ] Display results and sources 
- [ ] Basic usage monitoring

### Step 3.2: LLM Enhancement Layer
- [ ] Integrate OpenAI API (or local simulation)
- [ ] Format responses with context from search results
- [ ] Response formatting with citations
- [ ] Token counting and cost controls
- [ ] Toggle between RAG/RAG+LLM modes

**Deliverables**: Working CLI demo with optional LLM enhancement

---

## Implementation Details

### File Structure
```
/workbench/
├── config/
│   └── settings.py          # Environment configuration from .env
├── scripts/
│   └── reddit_pipeline.py   # Fetch Reddit data, clean text, generate embeddings
├── src/
│   ├── search.py            # Core semantic search logic
│   └── rag.py               # Format search results and sources
├── cli_demo.py              # Minimal CLI interface to test pipeline
├── docs/                    # Inline summaries and usage examples
├── .env.example             # Environment template
├── .gitignore               # Exclude .env and sensitive files
└── requirements.txt         # Dependencies

```

### Key Dependencies
```
# Core
sentence-transformers
pinecone-client  # Free tier only
openai  # Local simulation
praw  # Reddit API

# Data & Utils
pandas
python-dotenv
pytest
requests
```

### Phase Checkpoints
- **Phase 1**: Data pipeline functional test
- **Phase 2**: Search returning results
- **Phase 3**: RAG system working
- **Phase 4**: LLM integration complete
- **Final**: Complete zero-cost demo

### Risk Mitigation
- **API Rate Limits**: Implement caching and throttling
- **Vector Store Issues**: Local vector storage for development
- **Zero Cost Requirement**: Local-only implementation option
- **Time Constraints**: Extended timeline for thorough testing


## Documentation Plan (MVP)

- All documentation will be **inline** within code files.
- Each module/file includes:
  - **Purpose**: Short summary at the top of the file
  - **Function/Class Comments**: One-line `# comments` for public functions/classes
  - **Usage Examples**: Brief example at the bottom or in a `__main__` block
- No separate `.md` files for Phase 1–3 components yet
- All documentation must be human-reviewable and kept minimal


## Success Criteria
- [ ] Users can ask DIY questions and get relevant answers
- [ ] Semantic search returns relevant Reddit r/diy content
- [ ] AI generates helpful responses with source citations
- [ ] OpenAI integration works reliably
- [ ] Cost controls prevent budget overrun
- [ ] System handles 50+ concurrent queries
- [ ] All core components documented
