# Next Phase Playbook

## Phase 1: Test System End-to-End (No Real Integration)

### Step 1: Test Data Pipeline
```bash
# 1. Run ingestion (already working)
python scripts/ingest_pipeline.py

# 2. Verify JSONL output
head -5 reddit_data.jsonl
```

### Step 2: Test Embeddings Pipeline (Mock)
```bash
# 3. Run embeddings with test data
python tests/test_embeddings.py

# 4. Verify embeddings generation works
```

### Step 3: Test RAG Pipeline (Mock)
```bash
# 5. Test RAG orchestrator with mock data
python scripts/rag_orchestrator.py
```

**Expected**: All components work with test/mock data

---

## Phase 2: Add Real Integration

### Step 4: Set Up OpenAI Integration
```bash
# 6. Add OpenAI API key to .env
echo "OPENAI_API_KEY=your_key_here" >> .env

# 7. Test OpenAI connection
python tests/test_auth.py
```

### Step 5: Set Up Pinecone Integration
```bash
# 8. Add Pinecone credentials to .env
echo "PINECONE_API_KEY=your_key_here" >> .env
echo "PINECONE_ENVIRONMENT=us-east-1" >> .env
echo "PINECONE_INDEX_NAME=reddit-diy-embeddings" >> .env

# 9. Create Pinecone index
python -c "from scripts.vector_store import init_pinecone; init_pinecone()"
```

### Step 6: Update Embeddings Pipeline
```bash
# 10. Replace mock embeddings with real OpenAI calls
# Edit scripts/embeddings_pipeline.py to use real API
```

---

## Phase 3: Test System End-to-End (With Integration)

### Step 7: Full Pipeline Test
```bash
# 11. Run complete pipeline
python scripts/ingest_pipeline.py
python scripts/embeddings_pipeline.py
python scripts/rag_orchestrator.py
```

### Step 8: Validation
```bash
# 12. Test with sample queries
python scripts/rag_orchestrator.py
# Try: "How to strip paint from wood?"
# Try: "Best tools for DIY projects?"
```

### Step 9: Performance Check
```bash
# 13. Monitor API usage and costs
# 14. Check Pinecone index size
# 15. Verify response quality
```

---

## Quick Commands Summary

```bash
# Phase 1: Mock Testing
python scripts/ingest_pipeline.py
python tests/test_embeddings.py
python scripts/rag_orchestrator.py

# Phase 2: Integration Setup
# Add API keys to .env
python tests/test_auth.py
python -c "from scripts.vector_store import init_pinecone; init_pinecone()"

# Phase 3: Full Testing
python scripts/ingest_pipeline.py
python scripts/embeddings_pipeline.py
python scripts/rag_orchestrator.py
```

## Success Criteria

- ✅ Phase 1: All mock tests pass
- ✅ Phase 2: API connections work
- ✅ Phase 3: End-to-end queries return good answers with citations
