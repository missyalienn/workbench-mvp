# Reddit r/DIY Data Ingestion Process

This notebook walks through the complete process of ingesting DIY project data from Reddit's API, explaining what happens at each step and the key functions involved.

## Overview

The ingestion process transforms raw Reddit posts into clean, structured data ready for vector embedding and semantic search. We'll extract high-quality DIY content, clean it for better search performance, and store it efficiently for downstream processing.

---

## Understanding Reddit's Rate Limits (Critical Foundation)

**Before implementing any Reddit API calls**, you must understand rate limiting as it affects every step of the process.

### Rate Limit Details

Reddit enforces strict rate limits to prevent abuse and ensure fair access:

- **60 requests per minute** for OAuth applications
- **1 request per second** sustained rate (to be safe)
- Rate limits are **per IP address** and **per client_id**
- Exceeding limits returns **HTTP 429 (Too Many Requests)**
- Rate limit headers show remaining quota: `x-ratelimit-remaining`, `x-ratelimit-reset`

### What "Respecting Rate Limits" Means

- Never exceed 60 requests in any 60-second window
- Add delays between requests to stay well under the limit
- Monitor rate limit headers and back off when approaching limits
- Handle 429 responses gracefully with exponential backoff
- Cache responses to avoid redundant API calls

### Implementation Strategy

- Sleep 1-2 seconds between batches of requests
- Track request timestamps to calculate remaining quota
- Use PRAW's built-in rate limiting (it helps but isn't perfect)
- Implement custom throttling for large data ingestion

### Rate Limiting Best Practices

- Start conservative (1 request every 2 seconds)
- Monitor Reddit's rate limit headers in responses
- Log rate limit status for debugging
- Implement circuit breakers for persistent failures
- Consider batching multiple subreddits in one session

**Important**: Every code example below incorporates rate limiting from the start. This isn't an afterthought - it's built into the design.

---

## Step 1: Authentication & API Setup

**What's happening**: Establishing a connection to Reddit's REST API using OAuth2 credentials.

### Getting Reddit API Credentials (One-time setup)

Before we can access Reddit's API, we need to register our application and obtain credentials:

1. **Create Reddit App**: Go to https://www.reddit.com/prefs/apps
2. **Choose "script" type**: For personal use applications
3. **Get credentials**: Reddit provides `client_id` and `client_secret`
# 4. **Store these as environment variables in a `.env` file**

### Credential Storage & Management

*** Environment Variables + External Storage**:
```
# .env (references to system environment variables)
REDDIT_CLIENT_ID=${REDDIT_CLIENT_ID}
REDDIT_CLIENT_SECRET=${REDDIT_CLIENT_SECRET}
REDDIT_USER_AGENT=TestScript/1.0 by /u/redditusername
```

Then store actual secrets in:
- **macOS Keychain**: `security add-generic-password -a reddit_client_id -s reddit_api -w abc123def456gh78`
- **System Environment**: `export REDDIT_CLIENT_ID=abc123def456gh78` in `~/.zshrc`


**Security Best Practices**:
- `.env` file is listed in `.gitignore` (never committed to version control)
- File permissions set to 600 (readable only by owner)
- Credentials are scoped to least-privilege (Reddit script apps have limited read-only access)


**What PRAW handles automatically**:
- OAuth2 token exchange (we don't store access tokens)
- Token refresh when expired + session mgmt across requests
- Rate limit headers parsing

**Why this approach is secure**:
- Reddit script credentials have limited scope (read-only access to public data)
- Temporary tokens expire automatically + no user auth tokens stored 
- Local file system protection prevents unauthorized access

### Authentication Flow  

In this step, we create an authenticated session with Reddit's API servers. PRAW (Python Reddit API Wrapper) handles the OAuth2 token exchange automatically and manages the session state throughout our data collection process.

**Key concepts**:
- `praw.Reddit()`: Creates authenticated Reddit instance, handles token management automatically
- Authentication happens once and persists for the entire session
- **We don't manually store tokens** - PRAW handles this internally and securely

**Code Example**:
```python
# Load credentials from environment
client_id = os.getenv('REDDIT_CLIENT_ID')
client_secret = os.getenv('REDDIT_CLIENT_SECRET')

# Create authenticated Reddit instance
reddit = praw.Reddit(
    client_id=client_id,
    client_secret=client_secret,
    user_agent="TestScript/1.0 by /u/yourusername"
)
```

---

## Step 2: Data Extraction  

**What's happening**: Making paginated HTTP GET requests to Reddit's `/r/DIY/top` endpoint, parsing JSON responses.

This step involves creating lazy iterators that fetch data on-demand. Reddit's API returns posts in batches (typically 25-100 per request) with pagination tokens to fetch subsequent pages.

**Key concepts**:
- `subreddit()` creates a Subreddit object but doesn't make API calls yet
- `top()` returns a ListingGenerator - a lazy iterator that fetches data only when needed
- Each iteration makes HTTP requests like: `GET /r/DIY/top.json?t=year&limit=25&after=...`
- Post objects are populated from Reddit's JSON response fields including metadata

**Data fields extracted**:
- `post_id`: Reddit's unique post identifier for deduplication
- `title`: Post title containing project descriptions  
- `content`: Post body content (selftext) in markdown format
- `score`: Upvotes minus downvotes (quality indicator)
- `permalink`: Direct link to the Reddit post
- `comments`: Array of top 5 comments with:
  - `post_id`: Link back to parent post
  - `comment_id`: Unique comment identifier
  - `body`: Comment text content
  - `score`: Comment upvotes minus downvotes
  

**Code Example**:
```python
# Create lazy iterator for top posts
for submission in reddit.subreddit("diy").top(time_filter="month", limit=10):
    # Create post data structure
    post_data = {
        'post_id': submission.id,
        'title': submission.title,
        'content': submission.selftext,
        'score': submission.score,
        'permalink': f"https://reddit.com{submission.permalink}",
        'comments': []
    }
    
    # Extract top 5 comments
    submission.comments.replace_more(limit=0)
    for i, comment in enumerate(submission.comments):
        if i >= 5:
            break
        comment_data = {
            'post_id': submission.id,
            'comment_id': comment.id,
            'body': comment.body,
            'score': comment.score
        }
        post_data['comments'].append(comment_data)
    
    time.sleep(1.2)  # Rate limiting
```

---

## Step 3: Data Cleaning & Preprocessing

**What's happening**: Text normalization to improve search quality and remove noise from user-generated content.

Raw Reddit content contains markdown formatting, URLs, user mentions, and inconsistent whitespace that can interfere with semantic search. This step standardizes the text format and removes elements that don't contribute to searchable content.

**Key concepts**:
- Text concatenation combines title and body since titles often contain key project information
- Regular expressions (`re.sub()`) perform pattern matching and replacement
- URL removal prevents irrelevant links from polluting vector embeddings  
- Whitespace normalization handles inconsistent Reddit markdown formatting
- Reddit-specific elements (user mentions, subreddit links) are removed as they don't help with DIY content search

**Advanced cleaning considerations**:
- Remove Reddit markdown formatting (bold, italic, strikethrough)
- Handle special characters and emoji that may not embed well
- Preserve important technical terms and measurements
- Maintain readability while removing noise

**Code Example**:
```python
import re

def clean_text(title, content):
    # Combine title and content
    text = f"{title} {content}"
    
    # Remove URLs and Reddit formatting
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # Links
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Bold
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text
```

---

## Step 4: Data Storage

**What's happening**: Serializing Python objects to JSON format for persistent storage and later processing.

This step converts our Python data structures into a standardized format that can be stored on disk and easily loaded for subsequent processing steps like vector embedding generation.

**Key concepts**:
- `json.dump()` converts Python dictionaries/lists to JSON strings and writes to file
- File I/O creates persistent storage that survives program restarts
- Structured format enables easy loading and processing by other tools
- JSON is human-readable for debugging and widely supported across languages

**Data structure design**:
- Each post becomes a structured record with consistent fields
- Original content is preserved alongside cleaned versions
- Metadata includes quality indicators and source information
- Ingestion timestamps enable incremental updates
- Unique identifiers prevent duplicate processing

**Code Example**:
```python
import json
from datetime import datetime

# Structure data for storage
post_record = {
    'id': submission.id,
    'title': submission.title,
    'cleaned_content': clean_text(submission.title, submission.selftext),
    'score': submission.score,
    'created_utc': submission.created_utc,
    'ingested_at': datetime.now().isoformat(),
    'url': submission.url
}

# Save to JSON file
with open('reddit_data.json', 'w') as f:
    json.dump(all_posts, f, indent=2)
```

---

## Step 5: Error Handling & Resilience

**What's happening**: Implementing robust error handling to deal with network failures, API issues, and data anomalies gracefully.

Since we're dealing with external APIs and network requests, many things can go wrong. This step ensures our ingestion pipeline can handle failures gracefully and continue processing even when individual requests fail.

**Key concepts**:
- Exception handling catches network errors, API limits, and malformed responses
- Exponential backoff increases delay between retries to avoid overwhelming the API when it's struggling
- Graceful degradation allows partial data collection even when errors occur
- Circuit breakers prevent cascading failures by failing fast when the API is consistently down

**Error scenarios handled**:
- Network timeouts and connection errors
- HTTP 429 (Too Many Requests) responses (rate limits covered above)
- Malformed JSON responses from Reddit
- Deleted or private posts that return incomplete data
- Reddit API service outages or maintenance
- Temporary authentication failures

**Resilience strategies**:
- Retry with exponential backoff for transient errors
- Log detailed error information for debugging
- Continue processing other posts when individual posts fail
- Save partial results to avoid losing work during long-running ingestion
- Implement checkpoints to resume from last successful batch

**Code Example**:
```python
import time
import logging

def fetch_with_retry(submission_id, max_retries=3):
    for attempt in range(max_retries):
        try:
            submission = reddit.submission(id=submission_id)
            return submission
        except Exception as e:
            if attempt == max_retries - 1:
                logging.error(f"Failed to fetch {submission_id}: {e}")
                return None
            time.sleep(2 ** attempt)  # Exponential backoff
```

---

## Step 6: Data Validation & Quality Control

**What's happening**: Ensuring data integrity and filtering low-quality content before expensive vector processing.

Since vector embedding generation is computationally expensive, we filter out low-quality content early in the pipeline. This step validates data completeness and applies quality thresholds.

**Key concepts**:
- Content filtering removes noise before expensive embedding generation
- Validation ensures downstream processing won't fail on malformed data  
- Quality scoring helps prioritize better content for limited vector storage
- Required field validation prevents processing incomplete records

**Quality indicators**:
- Post score (upvotes - downvotes) as community approval metric
- Content length to filter out very short, low-effort posts
- Presence of actual content (not deleted/removed posts)
- Completeness of required metadata fields

**Code Example**:
```python
def validate_post(submission):
    # Quality checks
    if submission.score < 10:  # Minimum score threshold
        return False
    if len(submission.selftext) < 100:  # Minimum content length
        return False
    if submission.selftext in ['[deleted]', '[removed]']:
        return False
    
    # Required fields check
    required_fields = ['id', 'title', 'selftext', 'score']
    return all(hasattr(submission, field) for field in required_fields)
```

---

## Next Steps

After successful ingestion, the cleaned and validated data will be:
1. **Embedded**: Converted to vector representations using sentence transformers
2. **Indexed**: Stored in a vector database (Pinecone) for fast similarity search
3. **Searchable**: Made available through semantic search endpoints

The structured format created here enables efficient batch processing of embeddings and maintains traceability back to original Reddit sources for citation purposes.
