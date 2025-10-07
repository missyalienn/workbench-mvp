# Scripts Folder Overview

This document provides a comprehensive overview of all scripts in the `/scripts/` folder and their functionality within the Reddit DIY RAG pipeline.

## 📁 Scripts Folder Structure

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

## 🔄 Pipeline Flow

```
ingest_pipeline.py → embeddings_pipeline.py → rag_orchestrator.py
     (Reddit data)      (Vector embeddings)    (RAG answers)
```

## 📋 Detailed File Descriptions

### **Data Pipeline Files**

#### 1. `ingest_pipeline.py` (164 lines)
- **Purpose**: Fetches Reddit posts and comments from DIY subreddit
- **Function**: Downloads data via Reddit API (PRAW) and saves to JSONL format
- **Key Features**:
  - Reddit API integration with PRAW
  - Batch processing (100 posts per batch)
  - JSONL output format
  - Rate limiting and error handling
- **Output**: `reddit_data.jsonl` with posts and comments
- **Status**: ✅ Complete

#### 2. `embeddings_pipeline.py` (287 lines)
- **Purpose**: Converts text data to vector embeddings and stores in Pinecone
- **Key Functions**:
  - `generate_embeddings(jsonl_file)` - Creates OpenAI embeddings from JSONL
  - `upsert_to_pinecone(vectors_list)` - Stores vectors in Pinecone database
  - `_process_batch()` - Processes records in batches
  - `_generate_embedding_with_retry()` - Handles rate limiting
- **Key Features**:
  - OpenAI embeddings API integration
  - Pinecone vector database storage
  - Retry logic and rate limiting
  - Batch processing for efficiency
  - Environment variable configuration
- **Output**: Vector embeddings in Pinecone index
- **Status**: ✅ Complete

### **RAG Components**

#### 3. `vector_store.py` (156 lines) ✅ **COMPLETE**
- **Purpose**: Pinecone vector database operations
- **Key Functions**:
  - `semantic_search(query_embedding, top_k=5)` - Vector similarity search
  - `upsert_embeddings(embeddings)` - Store vectors in Pinecone
  - `init_pinecone()` - Connection management
- **Key Features**:
  - Pinecone API integration
  - Batch upsert operations
  - Error handling and retry logic
  - Environment variable configuration
- **Status**: ✅ Complete

#### 4. `llm_client.py` (158 lines) ✅ **COMPLETE**
- **Purpose**: OpenAI API operations
- **Key Functions**:
  - `generate_embedding(text)` - Text to vector conversion
  - `generate_chat_completion(messages)` - Chat API calls
  - `format_context_for_llm(search_results)` - Context formatting
  - `create_rag_messages(user_question, context)` - Message preparation
- **Key Features**:
  - OpenAI embeddings and chat API integration
  - Rate limiting and retry logic
  - Context formatting for RAG
  - Error handling
- **Status**: ✅ Complete

#### 5. `rag_orchestrator.py` (129 lines) ✅ **COMPLETE**
- **Purpose**: High-level RAG pipeline coordination
- **Key Functions**:
  - `answer_query(user_question)` - Main RAG function
  - `_extract_sources_from_answer()` - Citation extraction
- **Key Features**:
  - Orchestrates vector search + LLM generation
  - Citation support using `[source: post_id]` format
  - Error handling and response formatting
  - Structured output with sources and metadata
- **Output**: Contextual answers with citations
- **Status**: ✅ Complete

#### 6. `search.py` (11 lines) ⚠️ **PLACEHOLDER**
- **Purpose**: Semantic search functionality (planned)
- **Status**: Contains only TODO comments
- **Note**: Functionality is implemented in `vector_store.py`
- **Recommendation**: Can be removed

#### 7. `rag-pipeline.py` (20 lines) ⚠️ **PLACEHOLDER**
- **Purpose**: RAG integration (planned)
- **Status**: Contains only TODO comments
- **Note**: Functionality is implemented in `rag_orchestrator.py`
- **Recommendation**: Can be removed

### **Testing Files**

#### 6. `test_embeddings.py` (150 lines)
- **Purpose**: Tests the embeddings pipeline functionality
- **Key Functions**:
  - `create_test_jsonl()` - Creates test data
  - `test_generate_embeddings()` - Tests embedding generation
  - `test_upsert_to_pinecone()` - Tests Pinecone upsert
- **Key Features**:
  - Creates test data for validation
  - Tests embedding generation and Pinecone upsert
  - Validates pipeline functionality
- **Usage**: Run to verify embeddings pipeline works correctly
- **Status**: ✅ Complete

## 🚀 Usage Examples

### Running the Complete Pipeline

1. **Data Collection**:
   ```bash
   python scripts/ingest_pipeline.py
   ```

2. **Generate Embeddings**:
   ```bash
   python scripts/embeddings_pipeline.py
   ```

3. **Query the RAG System**:
   ```bash
   python scripts/rag_orchestrator.py
   ```

### Testing the Pipeline

```bash
# Run unit tests
python tests/test_ingest_pipeline.py
python tests/test_embeddings.py
python tests/test_auth.py
```

### Programmatic Usage

```python
from scripts.rag_orchestrator import answer_query

# Ask a question
result = answer_query("What's the best way to strip paint from wood?")
print(result['answer'])    # Generated answer with citations
print(result['sources'])   # List of sources used
```

## 🔧 Configuration

All scripts use environment variables for configuration:

- `REDDIT_CLIENT_ID` - Reddit API client ID
- `REDDIT_CLIENT_SECRET` - Reddit API client secret
- `REDDIT_USER_AGENT` - Reddit API user agent
- `OPENAI_API_KEY` - OpenAI API key
- `PINECONE_API_KEY` - Pinecone API key
- `PINECONE_ENVIRONMENT` - Pinecone environment (default: us-east-1)
- `PINECONE_INDEX_NAME` - Pinecone index name (default: reddit-diy-embeddings)

## ✅ Status Summary

| File | Status | Description |
|------|--------|-------------|
| `ingest_pipeline.py` | ✅ Complete | Reddit data collection |
| `embeddings_pipeline.py` | ✅ Complete | Vector embedding generation |
| `vector_store.py` | ✅ Complete | Pinecone operations |
| `llm_client.py` | ✅ Complete | OpenAI operations |
| `rag_orchestrator.py` | ✅ Complete | RAG coordination |
| `tests/test_ingest_pipeline.py` | ✅ Complete | Unit tests for ingest pipeline |
| `tests/test_embeddings.py` | ✅ Complete | Unit tests for embeddings |
| `tests/test_auth.py` | ✅ Complete | Authentication tests |
| `search.py` | ⚠️ Placeholder | Semantic search (functionality in vector_store.py) |
| `rag-pipeline.py` | ⚠️ Placeholder | RAG integration (functionality in rag_orchestrator.py) |

## 🎯 Next Steps

1. **Cleanup**: Consider removing or refactoring placeholder files (`search.py`, `rag-pipeline.py`)
2. **Integration**: Create a main orchestration script to run the complete pipeline
3. **Testing**: Add more comprehensive tests for the query pipeline
4. **Documentation**: Add API documentation for the query functions

## 📝 Notes

- The core RAG pipeline is fully functional through `rag_orchestrator.py`
- All placeholder functionality has been implemented in the main pipeline files
- The system supports end-to-end Reddit data → embeddings → semantic search → contextual answers
- Citations are automatically included in responses using `[source: post_id]` format
