
from clients  import get_openai_client
from openai import OpenAI


def embed_items(items):
    """
    Minimal function to embed a list of items using OpenAI text-embedding-3-small.
    
    Each item should be a dict with at least:
    - "id"
    - "text"
    - "source"
    
    Returns a list of dicts:
    {
        "id": ...,
        "embedding": [...],
        "metadata": {"text": ..., "source": ...}
    }
    """
    client = get_openai_client()

    # Extract all texts
    texts = [item["text"] for item in items]
    
    # Generate embeddings
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )
    
    # Combine embeddings with metadata
    embedded_items = []
    for item, emb_data in zip(items, response.data):
        embedded_items.append({
            "id": item["id"],
            "embedding": emb_data.embedding,
            "metadata": {
                "text": item["text"],
                "source": item["source"]
            }
        })
    
    return embedded_items

# Example usage with your 2-test-item list
test_items = [
    {
        "id": "post_1jjxjn6",
        "text": "My wife went to a work event for a few days, in my hubris I thought I could build her a new studio...",
        "source": "reddit"
    },
    {
        "id": "comment_mjqvv03",
        "text": ">completely finish this project in 5 days In my mind: Maybe do-able as long as you have a few reliable friends...",
        "source": "reddit"
    }
]

results = embed_items(test_items)
print(results)

