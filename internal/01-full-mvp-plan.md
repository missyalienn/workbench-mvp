# Workbench DIY MVP 

This checklist covers the end-to-end MVP build sequence, focusing on the backend and semantic search pipeline. UI work is intentionally left for last.  

---

## 1️⃣ API Keys & Environment Setup
- [ ] Obtain **OpenAI API key** and add to `.env`  
  - [ ] Test basic `text-embedding-3-small` call with dummy text  
  - [ ] Confirm response shape (embedding vector)  
- [ ] Obtain **Pinecone API key** and environment  
  - [ ] Create a test index (e.g., `diy-embeddings`)  
  - [ ] Confirm connection via Python client  
- [ ] Add all API keys to `.env` or secret manager  
- [ ] Confirm `dotenv` or equivalent works in your Python scripts  

---

## 2️⃣ Replace Mock Functions in Cursor
- [ ] Identify all mock functions/stubs:  
  - `mock_vector_search()`  
  - `fake_openai_call()`  
- [ ] Replace mocks with **real API calls**:  
  - [ ] Embedding calls → OpenAI embeddings API  
  - [ ] Vector search → Pinecone query (or in-memory test)  
  - [ ] LLM calls → OpenAI completion (or temporarily skip)  
- [ ] Test each function individually with dummy inputs  
- [ ] Ensure logging or print statements show outputs clearly  

---

## 3️⃣ Test End-to-End Semantic Search Locally (In-Memory)
- [ ] Load **small test JSONL dataset** (~100 posts)  
  - [ ] Confirm schema: `{id, title, body, comments[]}`  
- [ ] Embed all posts/comments using OpenAI embeddings  
- [ ] Store embeddings in **temporary in-memory vector store**  
- [ ] Run test queries:  
  - [ ] Example: “Best way to strip varnish”  
  - [ ] Verify top matches are reasonable  
- [ ] Adjust embedding parameters or cosine similarity threshold as needed  

---

## 4️⃣ Integrate Pinecone Vector Store
- [ ] Initialize Pinecone client with keys from `.env`  
- [ ] Create vector index for embeddings  
- [ ] Ingest small test dataset into Pinecone  
- [ ] Query Pinecone index with embeddings from sample queries  
- [ ] Confirm returned matches align with expected content  
- [ ] Implement basic error handling for API timeouts or empty results  

---

## 5️⃣ Pipeline Validation with Expanded Dataset
- [ ] Expand Reddit scraping:  
  - [ ] Increase number of posts (e.g., 1k–10k)  
  - [ ] Use multiple sort modes (`top`, `hot`, `new`)  
  - [ ] Keep "more comments" rule: ≥3 replies  
- [ ] Optional filtering:  
  - [ ] Minimum comment length (e.g., >20 chars)  
  - [ ] Minimum karma (e.g., ≥2)  
  - [ ] Remove one-word/emoji comments  
- [ ] Convert new dataset to JSONL  
- [ ] Test embedding and Pinecone ingestion  
- [ ] Run semantic search queries on this dataset to validate relevance  

---

## 6️⃣ LLM Integration for Summarization / Answering
- [ ] Optional: feed top-N retrieved posts/comments to OpenAI LLM  
- [ ] Summarize or answer a query based on retrieved context  
- [ ] Test for clarity, hallucination, or misalignment  
- [ ] Adjust prompt design if output quality is poor  

---

## 7️⃣ Logging & Debugging
- [ ] Add logging at each stage:  
  - API call success/failure  
  - Number of posts/comments processed  
  - Embedding shape & similarity scores  
- [ ] Confirm pipeline handles edge cases:  
  - Empty comments  
  - Posts with very long bodies  
  - Rate limits / API failures  

---

## 8️⃣ Documentation & Next Steps
- [ ] Document environment setup, keys, and usage  
- [ ] Document JSONL schema and preprocessing rules  
- [ ] Prepare notes for UI integration (Next step)  
- [ ] Outline dataset optimization ideas for future iteration  

---

### ✅ Notes
- Focus on making **pipeline end-to-end functional first**.  
- Don’t tweak Reddit filters until semantic search is proven working.  
- Keep UI for last; backend robustness is priority.  
