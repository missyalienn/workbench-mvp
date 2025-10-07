# API Integration Guide

This guide provides step-by-step instructions for integrating real OpenAI and Pinecone APIs into the Reddit DIY RAG pipeline.

## 🎯 Overview

**Goal**: Replace mock/test functionality with real API calls to OpenAI and Pinecone.

**Current Status**: 
- ✅ Reddit data collection working
- ✅ Unit tests passing
- ❌ OpenAI integration (placeholder)
- ❌ Pinecone integration (placeholder)

## 🔑 Step 1: Get API Keys

### OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up/Login
3. Navigate to **API Keys** section
4. Click **"Create new secret key"**
5. Copy the key (starts with `sk-...`)
6. **Important**: Save it immediately - you won't see it again

### Pinecone API Key
1. Go to [Pinecone Console](https://app.pinecone.io/)
2. Sign up/Login
3. Navigate to **API Keys** section
4. Copy your API key
5. Note your **Environment** (usually `us-east-1`)

## ⚙️ Step 2: Configure Environment Variables

### Create/Update .env File
```bash
# Navigate to project directory
cd /Users/mallan/dev/workbench-mvp

# Create .env file if it doesn't exist
touch .env

# Add your API keys (replace with your actual keys)
echo "REDDIT_CLIENT_ID=your_reddit_client_id" >> .env
echo "REDDIT_CLIENT_SECRET=your_reddit_client_secret" >> .env
echo "REDDIT_USER_AGENT=TestScript/1.0 by /u/yourusername" >> .env
echo "OPENAI_API_KEY=sk-your-actual-openai-key-here" >> .env
echo "PINECONE_API_KEY=your-actual-pinecone-key-here" >> .env
echo "PINECONE_ENVIRONMENT=us-east-1" >> .env
echo "PINECONE_INDEX_NAME=reddit-diy-embeddings" >> .env
```

### Verify .env File
```bash
# Check if .env file exists and has content
ls -la .env
cat .env
```

**Expected Output**:
```
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=TestScript/1.0 by /u/yourusername
OPENAI_API_KEY=sk-your-actual-openai-key-here
PINECONE_API_KEY=your-actual-pinecone-key-here
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=reddit-diy-embeddings
```

## 🧪 Step 3: Test API Connections

### Test OpenAI Connection
```bash
# Activate virtual environment
source venv/bin/activate

# Test OpenAI API
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
if api_key:
    print('✅ OpenAI API key found')
    print(f'Key starts with: {api_key[:10]}...')
else:
    print('❌ OpenAI API key not found')
"
```

### Test Pinecone Connection
```bash
# Test Pinecone API
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv('PINECONE_API_KEY')
if api_key:
    print('✅ Pinecone API key found')
    print(f'Key starts with: {api_key[:10]}...')
else:
    print('❌ Pinecone API key not found')
"
```

## 🔧 Step 4: Create Pinecone Index

### Create Index via Python
```bash
python -c "
import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))

# Create index
index_name = os.getenv('PINECONE_INDEX_NAME', 'reddit-diy-embeddings')
print(f'Creating index: {index_name}')

try:
    pc.create_index(
        name=index_name,
        dimension=1536,  # OpenAI embedding dimension
        metric='cosine',
        spec=ServerlessSpec(
            cloud='aws',
            region='us-east-1'
        )
    )
    print('✅ Index created successfully')
except Exception as e:
    if 'already exists' in str(e):
        print('✅ Index already exists')
    else:
        print(f'❌ Error creating index: {e}')
"
```

### Verify Index Creation
```bash
python -c "
import os
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))

# List indexes
indexes = pc.list_indexes()
print('Available indexes:')
for index in indexes:
    print(f'  - {index.name}')
"
```

## 🚀 Step 5: Test Full Pipeline

### Test 1: Generate Embeddings
```bash
# Test embeddings generation
python tests/test_embeddings.py
```

**Expected Output**:
```
🧪 Testing Embeddings Pipeline...
==================================================
🧪 Testing embedding generation...
✅ Created test file: /tmp/tmpXXXXXX.jsonl
✅ Generated 3 embeddings
   Vector 1: post_test1 - 1536 dimensions
   Vector 2: comment_test1 - 1536 dimensions
   Vector 3: post_test2 - 1536 dimensions
✅ All embeddings validated successfully

🧪 Testing Pinecone connection...
✅ Connected to Pinecone - found X indexes
==================================================
🎉 All tests passed! Embeddings pipeline is ready.
```

### Test 2: Run Full Embeddings Pipeline
```bash
# Generate embeddings for real data
python scripts/embeddings_pipeline.py
```

**Expected Output**:
```
Starting embeddings pipeline...
Loading JSONL file: reddit_data.jsonl
Processing 111 records in batches of 100...
Batch 1/2: Processing 100 records...
✅ Generated 100 embeddings
✅ Upserted 100 vectors to Pinecone
Batch 2/2: Processing 11 records...
✅ Generated 11 embeddings
✅ Upserted 11 vectors to Pinecone
Embeddings pipeline completed successfully!
```

### Test 3: Test RAG System
```bash
# Test RAG orchestrator
python scripts/rag_orchestrator.py
```

**Expected Output**:
```
Starting RAG orchestrator test...
Question: What's the best way to strip paint from wood?

Answer: Based on the Reddit discussions, the best way to strip paint from wood is to use a chemical stripper like Citristrip, which is safer than traditional strippers. Apply it thickly, let it sit for 30 minutes to 2 hours, then scrape it off with a putty knife. For stubborn areas, you may need to repeat the process. Always work in a well-ventilated area and wear protective gloves. [source: post_1jjxjn6]

Sources used:
1. post (ID: post_1jjxjn6)
   Score: 0.892
   Text: My wife went to a work event for a few days...
   URL: https://reddit.com/r/DIY/comments/1jjxjn6/...

RAG orchestrator test completed successfully!
```

## 🔍 Step 6: Verify Integration

### Check Pinecone Index
```bash
python -c "
import os
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index_name = os.getenv('PINECONE_INDEX_NAME', 'reddit-diy-embeddings')

# Connect to index
index = pc.Index(index_name)

# Get index stats
stats = index.describe_index_stats()
print(f'Index: {index_name}')
print(f'Total vectors: {stats.total_vector_count}')
print(f'Dimension: {stats.dimension}')
"
```

### Test Semantic Search
```bash
python -c "
import os
from dotenv import load_dotenv
from scripts.llm_client import generate_embedding
from scripts.vector_store import semantic_search

load_dotenv()

# Test query
query = 'How to build a bookshelf?'
print(f'Query: {query}')

# Generate query embedding
query_embedding = generate_embedding(query)
print(f'✅ Generated query embedding: {len(query_embedding)} dimensions')

# Search for similar content
results = semantic_search(query_embedding, top_k=3)
print(f'✅ Found {len(results)} results')

for i, result in enumerate(results, 1):
    print(f'{i}. {result[\"text\"][:100]}... (score: {result[\"score\"]:.3f})')
"
```

## 🐛 Troubleshooting

### Common Issues

#### 1. OpenAI API Key Issues
```bash
# Check if key is set
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('OPENAI_API_KEY:', 'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET')"

# Test API call
python -c "
import openai
import os
from dotenv import load_dotenv
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

try:
    response = openai.embeddings.create(
        input='test',
        model='text-embedding-3-small'
    )
    print('✅ OpenAI API working')
except Exception as e:
    print(f'❌ OpenAI API error: {e}')
"
```

#### 2. Pinecone API Key Issues
```bash
# Check if key is set
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('PINECONE_API_KEY:', 'SET' if os.getenv('PINECONE_API_KEY') else 'NOT SET')"

# Test Pinecone connection
python -c "
from pinecone import Pinecone
import os
from dotenv import load_dotenv
load_dotenv()

try:
    pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
    indexes = pc.list_indexes()
    print('✅ Pinecone API working')
    print(f'Found {len(indexes)} indexes')
except Exception as e:
    print(f'❌ Pinecone API error: {e}')
"
```

#### 3. Index Issues
```bash
# Check if index exists
python -c "
import os
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index_name = os.getenv('PINECONE_INDEX_NAME', 'reddit-diy-embeddings')

try:
    index = pc.Index(index_name)
    stats = index.describe_index_stats()
    print(f'✅ Index {index_name} exists')
    print(f'Total vectors: {stats.total_vector_count}')
except Exception as e:
    print(f'❌ Index error: {e}')
"
```

#### 4. Embedding Issues
```bash
# Test embedding generation
python -c "
from scripts.llm_client import generate_embedding

try:
    embedding = generate_embedding('test text')
    print(f'✅ Embedding generated: {len(embedding)} dimensions')
except Exception as e:
    print(f'❌ Embedding error: {e}')
"
```

## ✅ Success Checklist

- [ ] OpenAI API key obtained and set in `.env`
- [ ] Pinecone API key obtained and set in `.env`
- [ ] Pinecone index created successfully
- [ ] OpenAI API connection test passes
- [ ] Pinecone API connection test passes
- [ ] Embeddings generation test passes
- [ ] Full embeddings pipeline runs successfully
- [ ] RAG system returns answers with citations
- [ ] Semantic search returns relevant results

## 💰 Cost Considerations

### OpenAI Costs
- **Embeddings**: ~$0.0001 per 1K tokens
- **Chat API**: ~$0.0015 per 1K tokens
- **Estimated cost**: $1-5 for testing with 111 records

### Pinecone Costs
- **Free tier**: 1 index, 100K vectors
- **Paid tier**: $70/month for 1M vectors
- **Estimated cost**: Free for testing

## 🎯 Next Steps After Integration

1. **Test with more data**: Increase post limit in `ingest_pipeline.py`
2. **Optimize queries**: Fine-tune RAG prompts
3. **Add more features**: Implement advanced search
4. **Monitor usage**: Track API costs and performance
5. **Scale up**: Move to production environment

## 📞 Quick Commands Reference

```bash
# Essential integration commands
python tests/test_embeddings.py          # Test embeddings
python scripts/embeddings_pipeline.py    # Generate embeddings
python scripts/rag_orchestrator.py       # Test RAG system

# Verification commands
python -c "from scripts.llm_client import generate_embedding; print('OpenAI OK')"
python -c "from scripts.vector_store import semantic_search; print('Pinecone OK')"

# Index management
python -c "from pinecone import Pinecone; pc = Pinecone(api_key='your_key'); print(pc.list_indexes())"
```

## 🆘 Emergency Reset

If something goes wrong and you need to start over:

```bash
# Delete Pinecone index
python -c "
from pinecone import Pinecone
import os
from dotenv import load_dotenv
load_dotenv()
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index_name = os.getenv('PINECONE_INDEX_NAME', 'reddit-diy-embeddings')
pc.delete_index(index_name)
print('Index deleted')
"

# Recreate index
python -c "
from pinecone import Pinecone, ServerlessSpec
import os
from dotenv import load_dotenv
load_dotenv()
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index_name = os.getenv('PINECONE_INDEX_NAME', 'reddit-diy-embeddings')
pc.create_index(name=index_name, dimension=1536, metric='cosine', spec=ServerlessSpec(cloud='aws', region='us-east-1'))
print('Index recreated')
"
```
