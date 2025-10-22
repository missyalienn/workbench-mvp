

## 📝 TODO – Minimum Credible Data Filters for ingest_pipeline.py

### 1. Add constants and regex

✅  **Define allowed flairs and keywords**
  - Make ALLOWED_FLAIRS a set so membership checks can run quickly and the values are unique; 
  - sets are ideal for “is this flair allowed?” lookups. 
  - Make TITLE_KEYWORDS is a tuple because it’s a fixed, ordered list of phrases
  - It does not get mutated. The tuples make it clear the collection is read-only and keeps light footprint. 

```python 
    ALLOWED_FLAIRS = {"help", "question", "advice", "how to"}
    TITLE_KEYWORDS = ("how", "what", "why", "can", "should", "best way", "need help")
``` 

### 2. Add helper function 

### WHY? 
Because once the allowlist and keyword constants exist, the next logical step is to encapsulate the filtering logic that uses them. A helper function (e.g., is_howto_candidate) can reference ALLOWED_FLAIRS and TITLE_KEYWORDS in one place, keeping the main ingestion loop clean. By adding that helper right after the constants, you:

- keep related logic co-located, which aids readability;
- ensure any future tweak to flairs/keywords only requires touching one section;
- avoid scattering inline checks throughout the loop, reducing the risk of inconsistent filters.

Helper converts static configuration (allowlist + keywords) into a reusable predicate (a function that returns a BOOLEAN) the rest of the pipeline calls.


```python 
def is_howto_candidate(submission) -> bool:
    # Use clean_text on title/body
    # Check:
    # - flair in ALLOWED_FLAIR
    # - title matches TITLE_PATTERNS
    # - body has enough length
```
- Apply clean_text() to both title and body before checking
- Combine all conditions logically (flair, title match, body length)

## 3. In fetch_posts(...), add:

- if not is_howto_candidate(submission):
    continue


## 4. In build_dataset(...):

- 'flair': (submission.link_flair_text or "").lower()
if len(clean_comment_text) < 40:
    continue


## Add a second writer for filtered output:

- save_jsonl(dataset, filename="reddit_data_filtered.jsonl")












- Flair allowlist: keep posts where link_flair_text ∈ {"help", "question", "advice", "how to"} (case-insensitive).
- Title intent: keep if title contains ? or matches (how|what|why|can|should|best way|need help) (case-insensitive).
- Body/content: drop if selftext cleaned length < 80 chars unless title intent passes; drop media/link-only posts (selftext empty).
- Comments: drop if cleaned length < 40 chars.
- Metadata: store flair, len_text, and type in JSONL for audit and index-time filtering.
What to change/add in code

## scripts/ingest_pipeline.py
Add constants and an intent filter:

- ALLOWED_FLAIR = {"help","question","advice","how to"}
- TITLE_PATTERNS = re.compile(r"(how|what|why|can|should|best way|need help)", re.I)
- def is_howto_candidate(submission) -> bool: use clean_text on title/body; check flair/title/body/length.
In fetch_posts(...): if not is_howto_candidate(submission): continue
In build_dataset(...): include 'flair': (submission.link_flair_text or "").lower(), and for comments if len(clean_comment_text) < 40: continue.
Add a second writer save_jsonl(dataset, filename="reddit_data_filtered.jsonl") for the filtered run.
scripts/embeddings.py
Add def load_jsonl(path, allowed_types={"post","comment"}, flair_allow=None): to read a file, filter by type, optional flair allowlist.
Embed in batches (e.g., 128–256) and return [{"id", "embedding", "metadata": {"text","source","flair","type"}}].
Keep get_openai_client() usage and avoid printing full vectors; log counts only.
scripts/vectordb.py
Add a simple upsert_batch(items) and query(query_text, top_k=5, metadata_filter=None); pass metadata_filter with flair at query time to match ingestion filters. Keep index name and namespace configurable via .env.














## Concrete code hooks

In scripts/ingest_pipeline.py:24, declare the allowlist and keyword tuple.
Add a helper just below the Reddit client (before fetch_posts) that receives a submission, normalizes flair/title/body with clean_text, and returns True/False.
Update the loop inside fetch_posts to continue when the helper returns False, and persist the flair inside the post_record dictionary in build_dataset.
Optionally, make comment_record store parent_flair if we want to filter comments later by the post’s flair.

## Why this before Pinecone
These filters use signals you explored in api-sandbox/data_quality.py; they’re light-touch but carve out posts that actually ask for guidance. Running embeddings/search on this reduced set will give immediate feedback on search quality without re-ingesting the entire subreddit.

















## Why keep len_text in metadata? 
Short answer: store len_text (length of cleaned text) because it’s a cheap, high‑value signal for quality, ranking, and cost control.

- Quality gating: quickly drop thin content (e.g., posts with <80 chars; comments <40). Prevents low‑signal items from entering the corpus.
- Ranking/boosting: down‑weight very short items at query time so one‑line titles don’t outrank substantive replies.
- Index/query filters: add a Pinecone metadata filter like len_text >= 80 to constrain retrieval when needed.
- Debugging/audit: inspect length distributions to tune thresholds without re‑parsing text.
- Cost/ops control: approximate tokens (len_text/4) to cap/skip overly long items or decide when to chunk, keeping embedding costs predictable.

## Minimal code additions

- Add len_text and flair to records during ingestion, after cleaning.

How you’ll use it next

- Embedding: skip items below min length; optionally cap max length or chunk long items.
- Search: apply a metadata predicate (e.g., len_text >= 80) and add a small score boost proportional to log(len_text) to favor richer answers.
- Monitoring: print simple percentiles of len_text to tune thresholds as you scale.

You’re already storing type and url; adding flair and len_text keeps the metadata minimal but gives you strong controls over relevance and cost without extra dependencies.







In scripts/ingest_pipeline.py:96

post_text is already computed. Include calculated length and flair.
In scripts/ingest_pipeline.py:101
post_record = {
'id': f"post_{submission.id}",
'type': 'post',
'text': post_text,
'score': submission.score,
'source': 'reddit',
'url': f"https://reddit.com{submission.permalink}",
'created_at': submission.created_utc,
'flair': (getattr(submission, 'link_flair_text', '') or '').lower(),
'len_text': len(post_text)
}

In scripts/ingest_pipeline.py:116

Skip short comments and store their length.
clean_comment_text = clean_text(comment.body)
if len(clean_comment_text) < 40:
continue
comment_record = {
'id': f"comment_{comment.id}",
'type': 'comment',
'text': clean_comment_text,
'score': comment.score,
'link_id': f"post_{submission.id}",
'source': 'reddit',
'created_at': comment.created_utc,
'flair': (getattr(submission, 'link_flair_text', '') or '').lower(),
'len_text': len(clean_comment_text)
}

