
# Implement Reddit Data Pipeline

## Naming Conventions

For clarity, here’s how objects from PRAW are named and used throughout the pipeline:

- `reddit` → the PRAW Reddit client instance  
- `subreddit` → the result of `reddit.subreddit("diy")`  
- `submission` → a single post from the subreddit iterator  
- `posts_list` → the list of `submission` objects you fetch  
- `dataset` → your final `all_data` list  

Example: `reddit.subreddit("diy")` is how you access the subreddit inside your functions.

---

## TO DO

- [x] **Fetch top posts**  
  - Fetch top N (2000) posts from `r/diy` using PRAW  
  - Sleep 1.2 seconds between posts to respect Reddit API limits  
  - Implemented as: `fetch_posts(reddit, limit=2000)`  

- [x] **Fetch top comments**  
  - For each post (`submission`), fetch top 10 comments with PRAW best practices  
  - Use `threshold=3` to filter low-engagement threads  
  - Use `submission.comments.list()` to capture nested comments  
  - Add rate limit handling with try/except  
  - Implemented as: `fetch_comments(submission, limit=10)`  

- [x] **Clean text**  
  - Remove URLs, markdown, extra whitespace, and newlines  
  - Apply to post title, post content, and comments  
  - Implemented as: `clean_text(text)`  

- [x] **Build dataset**  
  - Combine posts (`submission`) and cleaned comments into a structured dataset  
  - Append each post to `dataset` 
  - Implemented as: `build_dataset(posts_list, comment_limit=10)`  

- [x] **Save to JSON**  
  - Save dataset (`dataset`) to JSON file  
  - Ensure valid JSON array structure  
  - Implemented as: `save_json(dataset, filename="reddit_data.json")`  

- [x] **Main orchestration**  
  - Initialize Reddit connection via PRAW  
  - Call `fetch_posts()`, `build_dataset()`, and `save_json()` in order  
  - Implemented as: `main()`


### Comment Selection Logic

1. **Top 10 Comments**  
   - Use `submission.comments.list()[:limit]` (with `limit=10`) to get the first 10 comments from the flattened comment list.

2. **"More Comments" Threshold**  
   - Call `submission.comments.replace_more(limit=0, threshold=3)` to expand "More Comments" only for threads with at least 3 comments.
   - Threads with 1–2 comments are skipped.

#### What This Means

- You receive the top 10 comments overall (including nested comments that meet the threshold).
- Nested threads with 3 or more comments are expanded.
- Low-engagement threads (1–2 comments) are skipped.
- The result is a flattened list of the top 10 comments, including qualifying nested comments.

---

## Current Implementation vs JSONL

**Current Issue**: Nested JSON array structure is inefficient for embedding/LLM workflows.

**JSONL Solution**: Flat records (one JSON object per line) enable:
- **Memory efficiency**: Stream processing vs loading entire file
- **Embedding generation**: Process records individually
- **Semantic search**: Each line is a searchable unit
- **LLM context**: Easy to format for prompts
- **Scalability**: Handle large datasets without memory issues

---

## JSON vs JSONL Analysis for Embedding/LLM Workflows

### Current vs JSONL Structure

#### Current Structure (Nested JSON Array)
```python
# Current: Single array with nested objects
[
  {
    "post_id": "1n695i4",
    "post_text": "I messed up, and I hate myself...",
    "comments": ["comment1", "comment2", ...],
    "score": 6661,
    "permalink": "https://reddit.com/..."
  }
]
```

#### Recommended JSONL Structure (Flat Records)
```python
# JSONL: One JSON object per line
{"id": "post_1n695i4", "type": "post", "text": "I messed up, and I hate myself...", "score": 6661, "source": "reddit", "url": "https://reddit.com/..."}
{"id": "comment_nbyf9dz", "type": "comment", "text": "Are you storing loose ball bearings...", "score": 13365, "parent_id": "post_1n695i4", "source": "reddit"}
{"id": "comment_nbyffta", "type": "comment", "text": "Is shelf.", "score": 803, "parent_id": "post_1n695i4", "source": "reddit"}
```

### Required Modifications

#### 1. **Modify `build_dataset()` Function**
```python
def build_dataset(posts_list, comment_limit=10):
    """Build flat dataset from posts and their comments."""
    print("Building dataset...")
    dataset = []
    
    for i, submission in enumerate(posts_list):
        # Get comments for this post
        comments = fetch_comments(submission, comment_limit)
        
        # Clean post title and content
        clean_title = clean_text(submission.title)
        clean_content = clean_text(submission.selftext)
        post_text = f"{clean_title} {clean_content}".strip()
        
        # Create post record (flat structure)
        post_record = {
            'id': f"post_{submission.id}",
            'type': 'post',
            'text': post_text,
            'score': submission.score,
            'source': 'reddit',
            'url': f"https://reddit.com{submission.permalink}",
            'created_utc': submission.created_utc
        }
        dataset.append(post_record)
        
        # Create comment records (flat structure)
        for comment in comments:
            clean_comment_text = clean_text(comment.body)
            if clean_comment_text:  # Only add non-empty comments
                comment_record = {
                    'id': f"comment_{comment.id}",
                    'type': 'comment',
                    'text': clean_comment_text,
                    'score': comment.score,
                    'parent_id': f"post_{submission.id}",
                    'source': 'reddit',
                    'created_utc': comment.created_utc
                }
                dataset.append(comment_record)
    
    print(f"Dataset built with {len(dataset)} records")
    return dataset
```

#### 2. **Replace `save_json()` with `save_jsonl()`**
```python
def save_jsonl(dataset, filename="reddit_data.jsonl", batch_size=100):
    """Save dataset to JSONL file in batches."""
    print(f"Saving dataset to {filename} in batches of {batch_size}...")
    
    # Process dataset in batches
    for i in range(0, len(dataset), batch_size):
        batch = dataset[i:i + batch_size]
        
        # Append batch to file (one JSON object per line)
        with open(filename, 'a', encoding='utf-8') as f:
            for record in batch:
                json.dump(record, f, ensure_ascii=False)
                f.write('\n')  # One record per line
        
        print(f"Saved batch {i//batch_size + 1}/{(len(dataset) + batch_size - 1)//batch_size} ({len(batch)} records)")
    
    print(f"Dataset saved to {filename} ({len(dataset)} total records)")
```

#### 3. **Update `main()` Function**
```python
def main():
    """Main function to orchestrate the Reddit data pipeline."""
    print("Starting Reddit data pipeline...")
    print(f"User Agent: {user_agent}")
    
    # Test Reddit connection
    try:
        reddit.user.me()
        print("Reddit API authentication successful.")
    except Exception as e:
        print(f"Reddit API authentication failed: {e}")
        return
    
    # Fetch posts
    posts_list = fetch_posts(reddit, limit=1000)
    
    # Build dataset
    dataset = build_dataset(posts_list, comment_limit=10)
    
    # Save to JSONL
    save_jsonl(dataset, filename="reddit_data.jsonl")
    
    print("Pipeline completed successfully!")
```

### Benefits for Your Workflow

#### 1. **Memory efficiency**
- Process one record at a time
- No need to load the entire file

#### 2. **Embedding generation**
```python
# Easy to process for embeddings
with open('reddit_data.jsonl', 'r') as f:
    for line in f:
        record = json.loads(line)
        if record['type'] == 'post':
            # Generate embedding for this post
            embedding = model.encode(record['text'])
```

#### 3. **Semantic search**
```python
# Easy to index individual records
with open('reddit_data.jsonl', 'r') as f:
    for line in f:
        record = json.loads(line)
        # Index this record in vector database
        index.upsert([(record['id'], embedding, record)])
```

#### 4. **LLM context building**
```python
# Easy to format for LLM prompts
def build_context(search_results):
    context = []
    for record in search_results:
        context.append(f"Post: {record['text']}")
        if record['type'] == 'comment':
            context.append(f"Comment: {record['text']}")
    return "\n".join(context)
```

### File Structure Changes

- **Before**: `reddit_data.json` (single array)
- **After**: `reddit_data.jsonl` (one JSON object per line)

### Additional Considerations

1. **Add metadata fields** for filtering and organization
2. **Include timestamps** for temporal analysis
3. **Add content type indicators** (post vs comment)
4. **Maintain parent-child relationships** via `parent_id`

This structure is better suited for embedding models, semantic search, and LLM workflows.