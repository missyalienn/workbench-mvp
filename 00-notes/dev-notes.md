# Dev Notes

Quick notes and learnings while building this project. 

---

## Writing Modular Code 

- Up until now, typically been writing quick inline code then extending later as project grows.
- It's time to evolve! 
- Goal: Write modular/reusable code whenever possible from the beginning! 

## Example: Not Modular Embedding Function 

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




## 🧪 Pytest Commands 
- `pytest tests/test_auth.py` — run all tests in file
- `pytest tests/test_auth.py::test_reddit_auth` — run a single test
- `pytest -k test_name` — run tests matching substring
- `pytest -x` — stop after first failure
- `pytest --maxfail=2` — stop after 2 failures
- `pytest -v` — verbose output

---

## 🔑 Auth & Secrets
- Store API keys in macOS Keychain with `keyring`
- Retrieve in Python:  
  ```python
  import keyring
  keyring.get_password("service", "username")
