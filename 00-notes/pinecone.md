## Pinecone Notes 

### Docs
[Pinecone API Docs](https://docs.pinecone.io/guides/get-started/quickstart)

[Retrieval-Augmented Generation with Pinecone, LangChain and OpenAI](https://colab.research.google.com/github/pinecone-io/examples/blob/master/docs/langchain-retrieval-augmentation.ipynb#scrollTo=v0to-QXCQjsm)

[Discord](https://discord.com/invite/tJ8V62S3sH?utm_medium=email&_hsenc=p2ANqtz--rjmasGDLG7LKZ14n4fcMHCF9fcRoYL0aNe8eZeNZEkMmyBK_Fc1E0tMjd7sA1W5n9noI-hRW394S_FqqYnAPDfAn2lg&_hsmi=329642830&utm_content=329642830&utm_source=hs_automation)

## 🧱 Creating an Index in Pinecone

Creating an index in Pinecone sets up a specialized search engine for vector embeddings. 
The index is the central structure that allows you to: 

- Store
- Retrieve
- Rank semantic vector chunks

### Key Parameters You Define When Creating an Index

- **Dimension**:  Size of your embedding vectors (e.g., 1536 for OpenAI embedding-3).

- **Metric**:  Similarity measurement method (e.g., `cosine`, `dot product`).

- **Vector Type**: Usually `"dense"` for semantic search.

- **Cloud & Region**: Specifies where Pinecone hosts the index (always cloud-hosted, even during local development).

### What You Can Do Once an Index Exists

- **Upsert Vectors:** Add or update vector data.
  
- **Query Vectors:** Retrieve nearest matches.
  
- **Delete/Update Entries:** Remove or modify indexed vectors.
  
- **Tag with Metadata:** Attach info such as source or type.


*Note: Pinecone indexes are always cloud-hosted. You can run code/tests locally but all index operations are performed remotely through Pinecone API.*