# Dev Notes

Quick notes and learnings while building this project. 

---

## Writing Modular Code 

- Up until now, typically been writing quick inline code then extending later as project grows.
- It's time to evolve! 
- Goal: Write modular/reusable code whenever possible from the beginning! 

## Example: Non-Modular Embedding Function 

``` python
from openai import OpenAI

api_key = "YOUR_API_KEY"
client = OpenAI(api_key=api_key)

# JSONL loaded somewhere here
with open("reddit_data_small.jsonl", "r") as f:
    records = [json.loads(line) for line in f]

embeddings = []
for record in records:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=record["text"]
    )
    embeddings.append(response.data[0].embedding)

```
**Issues:**
- Loops over JSONL directly in the middle of code — can’t easily reuse.
- No way to generate embeddings for any other text or dataset without copying this block.
- All logic is mixed together (loading data + generating embeddings).

## Importing Whole Modules vs. Just Classes 

### Style 1: Import Whole Module 

```python
import openai
import pinecone
import praw
import keyring

def get_openai_client():
    api_key = keyring.get_password("openai-key", "dev")
    return openai.OpenAI(api_key=api_key)       # note the module prefix

def get_pinecone_client():
    pc_key = keyring.get_password("pinecone-api-key", "dev")
    return pinecone.Pinecone(api_key=pc_key)   # module prefix here 

def get_reddit_client():
    client_id = keyring.get_password("reddit-client-id", "reddit-api")
    client_secret = keyring.get_password("reddit-client-secret", "reddit-api")
    user_agent = "TestScript/1.0 by /u/chippetto90"
    return praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)
```

## Style 2: Import Class Directly 

```python
import keyring
from praw import Reddit  # class imported directly
from openai import OpenAI
from pinecone import Pinecone

def get_openai_client():
    """Return OpenAI client."""
    api_key = keyring.get_password("openai-key", "dev")
    return OpenAI(api_key=api_key)

def get_pinecone_client():
    """Return Pinecone client."""
    pc_key = keyring.get_password("pinecone-api-key", "dev")
    return Pinecone(api_key=pc_key)

def get_reddit_client():
    """Return PRAW Reddit client."""
    client_id = keyring.get_password("reddit-client-id", "reddit-api")
    client_secret = keyring.get_password("reddit-client-secret", "reddit-api")
    user_agent = "TestScript/1.0 by /u/chippetto90"
    # Can reference class directly
    return Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)
```
---

## 🔑 Keyring Auth
- Store API keys in macOS Keychain with `keyring`
- Retrieve in Python:  
  ```python
  import keyring
  keyring.get_password("service", "username")

## 🧪 Pytest Commands 
- `pytest tests/test_auth.py` — run all tests in file
- `pytest tests/test_auth.py::test_reddit_auth` — run a single test
- `pytest -k test_name` — run tests matching substring
- `pytest -x` — stop after first failure
- `pytest --maxfail=2` — stop after 2 failures
- `pytest -v` — verbose output
