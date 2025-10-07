# 📝 OpenAI Embeddings – Quick Notes

## 1. What are embeddings?
- Numeric vector representing text meaning in semantic space.
- Used for: semantic search, similarity comparisons, recommendation engines, anomaly detection.

---

## 2. Minimal API Call Example

```python
from openai import OpenAI
import json

client = OpenAI()

response = client.embeddings.create(
    input="Hello world",
    model="text-embedding-3-small"
)
```
### Quick view: trim embedding for readability

```python
response_dict = response.to_dict()
for item in response_dict["data"]:
    item["embedding"] = item["embedding"][:5]

print(json.dumps(response_dict, indent=2))
```
---

## 3. Key Fields in Response
- **data**: List of embedding objects (one per input string)
- **data[0].embedding**: The numeric vector (embedding) itself
- **index**: Position of the input string in the original request
- **model**: Model used for embedding
- **usage**: Token usage counts

---

## 4. Quick Tips
- Trim embeddings for easier reading in notes or debugging.
- Multiple inputs → `data` will have multiple entries, in order.
- Use AI to generate boilerplate, but review and understand each line.
- Print the full JSON response to explore the structure before integrating.

---

## 5. Resources

- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)