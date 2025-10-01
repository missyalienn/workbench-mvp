# Testing Guide

This guide provides step-by-step instructions for testing the Reddit DIY RAG pipeline system.

Python Docs Unit Test Mock:  https://docs.python.org/3/library/unittest.mock.html

## 🚀 Quick Start

### 1. Check Current Status
```bash
# Check current branch
git branch

# Check if you're in the right directory
pwd
# Should be: /Users/mallan/dev/workbench-mvp
```

### 2. Activate Virtual Environment
```bash
source venv/bin/activate
```

## 🧪 Phase 1: Unit Tests (No API Keys Required)

### Test 1: Ingest Pipeline Functions
```bash
python tests/test_ingest_pipeline.py
```
**Expected**: All 18 tests pass ✅

### Test 2: Embeddings Pipeline (Mock)
```bash
python tests/test_embeddings.py
```
**Expected**: Tests pass or skip if no API keys ✅

### Test 3: Authentication Test
```bash
python tests/test_auth.py
```
**Expected**: Tests pass or skip if no API keys ✅

## 🔧 Phase 2: Data Pipeline Testing

### Test 4: Data Collection
```bash
# Check if data already exists
ls -la reddit_data.jsonl

# If no data, run ingestion (requires Reddit API keys)
python scripts/ingest_pipeline.py
```
**Expected**: Creates `reddit_data.jsonl` with 111 lines ✅

### Test 5: Verify Data Structure
```bash
# Check first few lines
head -3 reddit_data.jsonl

# Count total lines
wc -l reddit_data.jsonl
```
**Expected**: Valid JSON objects, one per line ✅

## 🔑 Phase 3: API Integration Testing

### Step 1: Set Up API Keys
```bash
# Check if .env file exists
ls -la .env

# If missing, create it with your API keys
echo "REDDIT_CLIENT_ID=your_reddit_client_id" >> .env
echo "REDDIT_CLIENT_SECRET=your_reddit_client_secret" >> .env
echo "REDDIT_USER_AGENT=TestScript/1.0 by /u/yourusername" >> .env
echo "OPENAI_API_KEY=your_openai_api_key" >> .env
echo "PINECONE_API_KEY=your_pinecone_api_key" >> .env
echo "PINECONE_ENVIRONMENT=us-east-1" >> .env
echo "PINECONE_INDEX_NAME=reddit-diy-embeddings" >> .env
```

### Step 2: Test API Connections
```bash
# Test Reddit API
python tests/test_auth.py

# Test OpenAI API
python tests/test_embeddings.py
```

### Step 3: Full Pipeline Test
```bash
# Generate embeddings and store in Pinecone
python scripts/embeddings_pipeline.py

# Test RAG system
python scripts/rag_orchestrator.py
```

## 🎯 Phase 4: End-to-End Testing

### Test 6: RAG Query System
```bash
python scripts/rag_orchestrator.py
```
**Try these sample queries:**
- "What's the best way to strip paint from wood?"
- "How to build a simple bookshelf?"
- "Best tools for DIY projects?"

**Expected**: Answers with citations like `[source: post_123]` ✅

## 🔄 Branch Management

### Switch Between Branches
```bash
# Switch to embeddings branch for embeddings work
git checkout embeddings

# Switch back to tests branch if needed
git checkout tests

# Check current branch
git branch
```

### Pull Latest Changes
```bash
# Pull latest changes from remote
git pull origin main

# Or pull from specific branch
git pull origin embeddings
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# If you get import errors, check Python path
python -c "import sys; print(sys.path)"

# Make sure you're in the right directory
pwd
```

#### 2. API Key Issues
```bash
# Check if .env file is loaded
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('OPENAI_API_KEY:', 'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET')"
```

#### 3. Virtual Environment Issues
```bash
# Reactivate virtual environment
source venv/bin/activate

# Check Python version
python --version
```

#### 4. Test Failures
```bash
# Run tests with verbose output
python -m unittest tests.test_ingest_pipeline -v

# Run specific test
python -m unittest tests.test_ingest_pipeline.TestIngestPipeline.test_clean_text_basic -v
```

## ✅ Success Criteria

### Phase 1 Complete When:
- [ ] All unit tests pass
- [ ] No import errors
- [ ] Test files are in `tests/` directory

### Phase 2 Complete When:
- [ ] Data pipeline runs without errors
- [ ] `reddit_data.jsonl` is created/updated
- [ ] Data structure is valid JSONL

### Phase 3 Complete When:
- [ ] API connections work
- [ ] Embeddings are generated
- [ ] Pinecone index is populated

### Phase 4 Complete When:
- [ ] RAG system returns answers
- [ ] Citations are included in responses
- [ ] End-to-end pipeline works

## 📝 Notes

- **Unit tests** don't require API keys and should always pass
- **Integration tests** require API keys and may skip if not available
- **Full pipeline** requires all API keys to be set
- **Data files** (`*.jsonl`) are excluded from git and won't be committed
- **Virtual environment** must be activated before running any Python commands

## 🆘 If Something Goes Wrong

1. **Check the error message** - it usually tells you what's wrong
2. **Verify API keys** - make sure they're set in `.env`
3. **Check virtual environment** - make sure it's activated
4. **Check file paths** - make sure you're in the right directory
5. **Check branch** - make sure you're on the right branch
6. **Pull latest changes** - make sure you have the latest code

## 📞 Quick Commands Reference

```bash
# Essential commands
git branch                    # Check current branch
source venv/bin/activate     # Activate virtual environment
python tests/test_ingest_pipeline.py  # Run unit tests
python scripts/ingest_pipeline.py     # Run data pipeline
python scripts/rag_orchestrator.py    # Test RAG system

# Branch switching
git checkout embeddings       # Switch to embeddings branch
git checkout tests           # Switch to tests branch
git checkout main            # Switch to main branch

# Status checks
ls -la reddit_data.jsonl     # Check if data exists
wc -l reddit_data.jsonl      # Count data lines
head -3 reddit_data.jsonl    # Preview data
```
