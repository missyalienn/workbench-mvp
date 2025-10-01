# System Flow Reference

This document provides a consolidated overview of the Reddit DIY RAG pipeline system flow, including both pipeline processes and runtime processes.

## 🔄 Complete System Flow

```
Reddit API → ingest-pipeline.py → reddit_data.jsonl
                                    ↓
Pinecone ← embeddings-pipeline.py ← JSONL data
    ↓
User Query → rag_orchestrator.py → vector_store.py → semantic search
                                    ↓
                              llm_client.py → OpenAI → Answer + Citations
```

## 📋 Pipeline Processes (Data Preparation)

### 1. Data Ingestion (`ingest_pipeline.py`)
- **Purpose**: Fetches Reddit posts and comments from r/diy subreddit
- **Process**:
  - Connects to Reddit API via PRAW
  - Fetches top posts (configurable limit, currently 10 for testing)
  - Retrieves top comments per post (limit 10)
  - Cleans text (removes URLs, markdown, normalizes whitespace)
  - Saves to `reddit_data.jsonl` (flat records, one JSON per line)
- **Output**: `reddit_data.jsonl` with structured posts and comments
- **Status**: ✅ Complete

### 2. Embeddings Generation (`embeddings_pipeline.py`)
- **Purpose**: Converts text data to vector embeddings and stores in Pinecone
- **Process**:
  - Reads JSONL file line by line
  - Generates OpenAI embeddings for each text record
  - Batches embeddings for efficient processing
  - Stores vectors in Pinecone vector database
- **Output**: Vector embeddings in Pinecone index
- **Status**: ✅ Complete

## 🚀 Runtime Processes (Query Processing)

### 3. Vector Search (`vector_store.py`)
- **Purpose**: Performs semantic search using vector similarity
- **Process**:
  - Takes user query
  - Generates query embedding via OpenAI
  - Searches Pinecone for similar vectors
  - Returns top-k most similar posts/comments
- **Output**: Ranked list of relevant content
- **Status**: ✅ Complete

### 4. LLM Processing (`llm_client.py`)
- **Purpose**: Generates contextual answers using OpenAI Chat API
- **Process**:
  - Formats search results as context
  - Creates RAG prompt with user question + context
  - Generates answer via OpenAI Chat API
  - Handles rate limiting and retries
- **Output**: Generated answer with context
- **Status**: ✅ Complete

### 5. RAG Orchestration (`rag_orchestrator.py`)
- **Purpose**: Coordinates the complete RAG pipeline
- **Process**:
  - Takes user question
  - Performs semantic search via vector_store.py
  - Formats context via llm_client.py
  - Generates final answer with citations
  - Returns structured response
- **Output**: Answer with citations in format `[source: post_id]`
- **Status**: ✅ Complete

## 🎯 Usage Patterns

### Setup (One-time)
```bash
# 1. Collect Reddit data
python scripts/ingest_pipeline.py

# 2. Generate embeddings and store in Pinecone
python scripts/embeddings_pipeline.py
```

### Query (Per Question)
```bash
# Run RAG system interactively
python scripts/rag_orchestrator.py
```

### Programmatic Usage
```python
from scripts.rag_orchestrator import answer_query

result = answer_query("What's the best way to strip paint from wood?")
print(result['answer'])    # Generated answer with citations
print(result['sources'])   # List of sources used
```

## 🔧 Configuration

All scripts use environment variables:

- `REDDIT_CLIENT_ID` - Reddit API client ID
- `REDDIT_CLIENT_SECRET` - Reddit API client secret
- `REDDIT_USER_AGENT` - Reddit API user agent
- `OPENAI_API_KEY` - OpenAI API key
- `PINECONE_API_KEY` - Pinecone API key
- `PINECONE_ENVIRONMENT` - Pinecone environment (default: us-east-1)
- `PINECONE_INDEX_NAME` - Pinecone index name (default: reddit-diy-embeddings)

## 📊 Data Flow

### Input Data Structure
```json
{"id": "post_1jjxjn6", "type": "post", "text": "My wife went to a work event...", "score": 77929, "source": "reddit", "url": "https://reddit.com/...", "created_at": 1742944839.0}
{"id": "comment_mjqvv03", "type": "comment", "text": ">completely finish this project...", "score": 11881, "link_id": "post_1jjxjn6", "source": "reddit", "created_at": 1742945801.0}
```

### Output Data Structure
```json
{
  "answer": "Based on the Reddit discussions, the best way to strip paint from wood is... [source: post_1jjxjn6]",
  "sources": ["post_1jjxjn6", "comment_mjqvv03"],
  "metadata": {
    "query": "How to strip paint from wood?",
    "search_results_count": 5,
    "processing_time": 2.3
  }
}
```

## 🧪 Testing

### Test Embeddings Pipeline
```bash
python tests/test_embeddings.py
```

### Test Authentication
```bash
python tests/test_auth.py
```

### Test Ingest Pipeline
```bash
python tests/test_ingest_pipeline.py
```

## 📁 File Structure

```
scripts/
├── ingest_pipeline.py      # Reddit data collection
├── embeddings_pipeline.py  # Vector embedding generation
├── vector_store.py         # Pinecone operations
├── llm_client.py          # OpenAI operations
└── rag_orchestrator.py    # RAG coordination

tests/
├── test_ingest_pipeline.py # Unit tests for ingest pipeline
├── test_embeddings.py      # Unit tests for embeddings
└── test_auth.py           # Authentication tests
```

## ✅ Current Status

| Component | Status | Description |
|-----------|--------|-------------|
| Data Ingestion | ✅ Complete | Reddit API → JSONL |
| Embeddings | ✅ Complete | JSONL → Pinecone |
| Vector Search | ✅ Complete | Semantic similarity |
| LLM Processing | ✅ Complete | Context → Answer |
| RAG Orchestration | ✅ Complete | End-to-end pipeline |
| Testing | ✅ Complete | Validation scripts |

## 🔄 Development Workflow

1. **Data Collection**: Run `ingest_pipeline.py` to collect fresh data
2. **Embeddings**: Run `embeddings_pipeline.py` to generate vectors
3. **Testing**: Use `tests/test_embeddings.py` to validate pipeline
4. **Querying**: Use `rag_orchestrator.py` for end-to-end testing
5. **Iteration**: Modify components and re-test as needed

## 🎯 Key Features

- ✅ Reddit API integration with PRAW
- ✅ OpenAI embeddings and chat API integration
- ✅ Pinecone vector database operations
- ✅ Semantic search with similarity scoring
- ✅ Context-aware answer generation
- ✅ Citation support with source tracking
- ✅ Error handling and retry logic
- ✅ Rate limiting for API calls
- ✅ Environment variable configuration
- ✅ Batch processing for efficiency
- ✅ Comprehensive testing

## 📝 Notes

- The system is fully functional and ready for production use
- All components are modular and can be tested independently
- Citations are automatically included in responses
- The pipeline supports both interactive and programmatic usage
- Data files (`*.jsonl`) are excluded from version control
