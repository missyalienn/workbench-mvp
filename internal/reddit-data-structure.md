# Reddit Data Structure Documentation

## Overview
This document describes the flat JSONL data structure used to store Reddit posts and comments in the Workbench DIY project.

## Data Flow
```
submission (Reddit API object) → flat records → JSONL file (one record per line)
```

## JSONL Format Structure

### File Format
The data is stored in JSONL (JSON Lines) format where each line contains a single JSON object representing either a post or a comment.

### Post Record Structure
```json
{
    "id": "post_1n695i4",
    "type": "post",
    "text": "I messed up, and I hate myself Shoud've turned the support studs...",
    "score": 6661,
    "source": "reddit",
    "url": "https://reddit.com/r/DIY/comments/1n695i4/i_messed_up_and_i_hate_myself/",
    "created_at": 1705312200.0
}
```

### Comment Record Structure
```json
{
    "id": "comment_nbyf9dz",
    "type": "comment",
    "text": "Are you storing loose ball bearings on the shelves? No? Then it's good enough.",
    "score": 13365,
    "link_id": "post_1n695i4",
    "source": "reddit",
    "created_at": 1705315800.0
}
```

### Field Definitions

#### Common Fields (All Records)
- **`id`** (string): Unique identifier prefixed with `post_` or `comment_` + Reddit ID
- **`type`** (string): Record type - either `"post"` or `"comment"`
- **`text`** (string): Cleaned text content (title + content for posts, body for comments)
- **`score`** (integer): Reddit upvotes/downvotes score
- **`source`** (string): Always `"reddit"`
- **`created_at`** (float): Unix timestamp from Reddit's `created_utc`

#### Post-Specific Fields
- **`url`** (string): Full Reddit permalink URL

#### Comment-Specific Fields
- **`link_id`** (string): Parent post ID (prefixed with `post_`) to maintain relationships

### Example JSONL File Content
```jsonl
{"id": "post_1n695i4", "type": "post", "text": "I messed up, and I hate myself Shoud've turned the support studs...", "score": 6661, "source": "reddit", "url": "https://reddit.com/r/DIY/comments/1n695i4/i_messed_up_and_i_hate_myself/", "created_at": 1705312200.0}
{"id": "comment_nbyf9dz", "type": "comment", "text": "Are you storing loose ball bearings on the shelves? No? Then it's good enough.", "score": 13365, "link_id": "post_1n695i4", "source": "reddit", "created_at": 1705315800.0}
{"id": "comment_nbyffta", "type": "comment", "text": "Is shelf.", "score": 803, "link_id": "post_1n695i4", "source": "reddit", "created_at": 1705316400.0}
{"id": "post_1n6a2b3", "type": "post", "text": "DIY Bookshelf Completed! Built my first bookshelf from scratch. Used pine and oak for the frame.", "score": 2450, "source": "reddit", "url": "https://reddit.com/r/DIY/comments/1n6a2b3/diy_bookshelf_completed/", "created_at": 1705320000.0}
{"id": "comment_nbz1abc", "type": "comment", "text": "Looks great! How long did it take you?", "score": 210, "link_id": "post_1n6a2b3", "source": "reddit", "created_at": 1705323600.0}
```


## Key Points

### Data Types
- **Strings**: id, type, text, source, url, link_id
- **Integers**: score
- **Floats**: created_at (Unix timestamp)
- **JSON Objects**: Each line in the JSONL file

### Flat Structure Benefits
- **Memory Efficient**: Process one record at a time
- **Streamable**: No need to load entire file into memory
- **Embedding Ready**: Each record can be processed individually
- **Search Friendly**: Each line is a searchable unit
- **LLM Compatible**: Easy to format for prompts

### Unicode Handling
- Text may contain Unicode escape sequences like `\u2019` (smart quotes)
- Text cleaning normalizes these to standard ASCII characters

## Usage Examples

### Reading JSONL File
```python
import json

# Process records one at a time
with open('reddit_data.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        record = json.loads(line.strip())
        if record['type'] == 'post':
            print(f"Post: {record['text'][:100]}...")
        elif record['type'] == 'comment':
            print(f"Comment: {record['text'][:100]}...")
```

### Filtering by Type
```python
# Get only posts
posts = []
with open('reddit_data.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        record = json.loads(line.strip())
        if record['type'] == 'post':
            posts.append(record)

# Get only comments
comments = []
with open('reddit_data.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        record = json.loads(line.strip())
        if record['type'] == 'comment':
            comments.append(record)
```

### Finding Related Records
```python
# Find all comments for a specific post
post_id = "post_1n695i4"
related_comments = []

with open('reddit_data.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        record = json.loads(line.strip())
        if record['type'] == 'comment' and record['link_id'] == post_id:
            related_comments.append(record)
```

### Building Context for LLM
```python
def build_context(post_id, max_comments=5):
    """Build context string for LLM from post and its comments."""
    context_parts = []
    
    with open('reddit_data.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            record = json.loads(line.strip())
            
            if record['id'] == post_id:
                context_parts.append(f"Post: {record['text']}")
            elif record['type'] == 'comment' and record['link_id'] == post_id:
                if len(context_parts) < max_comments + 1:  # +1 for post
                    context_parts.append(f"Comment: {record['text']}")
    
    return "\n\n".join(context_parts)
```

## Storage
- **Format**: JSONL (JSON Lines) - one JSON object per line
- **Filename**: `reddit_data.jsonl`
- **Processing**: Each line can be processed independently
- **Batching**: Records are saved in batches of 100 for efficiency

## Related Files
- `scripts/ingest-pipeline.py`: Creates JSONL records from Reddit API
- `scripts/test_jsonl.py`: Validates JSONL format and structure
- `reddit_data.jsonl`: Contains the serialized records

## Testing
Run the test script to validate the JSONL output:
```bash
python scripts/test_jsonl.py
```

This will verify:
- Each line is valid JSON
- Required fields are present
- ID formats are correct
- Records can be processed individually
