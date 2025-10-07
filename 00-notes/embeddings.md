
## 📝 Embeddings API Notes 
Notes on how embeddings work and how to use OpenAI embeddings API

>### ✨ Read the docs, pal! ✨  
> - [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
> - [API Reference - Embeddings Endpoint](https://platform.openai.com/docs/api-reference/embeddings)
> - [Use Cases](https://platform.openai.com/docs/guides/embeddings#use-cases)

### What are embeddings?

OpenAI’s text embeddings measure the relatedness of text strings. Embeddings are commonly used for:

- **Search**: Results are ranked by relevance to a query string.
- **Clustering**: Text strings are grouped by similarity.
- **Recommendations**: Items with related text strings are recommended.
- **Anomaly detection**: Outliers with little relatedness are identified.
- **Diversity measurement**: Similarity distributions are analyzed.
- **Classification**: Text strings are classified by their most similar label.

An **embedding** is a vector (list) of floating point numbers. The distance between two vectors measures their relatedness:  
- **Small distances** suggest high relatedness  
- **Large distances** suggest low relatedness

- Each embedding vector **encodes the meaning of the text**. These vectors can be compared to find similar content, power recommendation engines, detect anomalies, and perform other semantic tasks

### Example: Get embeddings
To get an embedding, send your text string to the embeddings API endpoint along with the embedding model name (e.g., text-embedding-3-small):

```python 
from openai import OpenAI
client = OpenAI()

response = client.embeddings.create(
    input="Your text string goes here",
    model="text-embedding-3-small"
)

print(response.data[0].embedding)
```
---

### Response Structure 

1. `response` is an object returned by `client.embeddings.create(...)`
   
2. `response.data` is a list of embedding objects, one per input string.
   
3. `response.data[0]` is the embedding of the first input string. 
   
4. `.embedding` is the numeric vector itself (list of thousands of floats. For embeddings-small = 1536).
   - For text-embeddings-3-small - length of embedding vector is 1536
   - For text-embedding-3-large - length of an embedding vector is 3072  
   - To reduce the embedding's dimensions without losing its concept-representing properties, pass in the dimensions parameter. 


---


### Example: single string input
```python
from openai import OpenAI

client = OpenAI()

response = client.embeddings.create(
    input="Your text string goes here",
    model="text-embedding-3-small"
)
```
Since we only passed one string, use `index 0` to access it:
```python
print(response.data[0].embedding)
```
This prints list of floating-point numbers—the actual embedding vector. Each number is a single dimension in the high-dimensional vector that represents the input text in semantic space.

--- 

### Example: multiple strings input
```python
inputs = ["Text 1", "Text 2", "Text 3"]
response = client.embeddings.create(
    input=inputs,
    model="text-embedding-3-small"
)
```
Each element in `response.data` corresponds to one input string:
```python
print("Embedding for Text 1:", response.data[0].embedding)
print("Embedding for Text 2:", response.data[1].embedding)
print("Embedding for Text 3:", response.data[2].embedding)
```
---

### Example: Print full response object with trimmed embeddings 
- Convert to a dictionary: allows you to manipulate the response easily.  
- Trim the embedding vector: show only a few floats in the embedding for readability 
- Print as JSON: allows us to see the full response structure including metadata and embeddings.  

```python
response_dict = response.to_dict()
for item in response_dict["data"]:
    item["embedding"] = item["embedding"][:3]
print(json.dumps(response_dict, indent=2))
```

**Example output (trimmed):**
```json
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "index": 0,
      "embedding": [-0.0069, -0.0053, -0.000045, -0.024, 0.0012]
    }
  ],
  "model": "text-embedding-3-small"
}
