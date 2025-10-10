## Auth to pinecone and create an index 

import keyring
from pinecone import Pinecone, ServerlessSpec

# Initialize a Pinecone client with API key
pc_key = keyring.get_password("pinecone-api-key", "dev")
pc = Pinecone(api_key=pc_key)

#Create index
index_name = "workbench-mvp"

try: 
# Create index
    if not pc.has_index(index_name):
        pc.create_index(
            name= index_name,
            vector_type="dense",
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            ),
            deletion_protection="disabled",
            tags={
                "environment": "development"
            }
        )
        print(f"Created index: {index_name}")
    else:
        print(f"⚠️ Index already exists: {index_name}")
except Exception as e: 
    print(f"❌ Index creation failed: {type(e).__name__} - {e}")

#Experimental - Get index
#take index_name as param 
#use pinecone client to get the index object (pc.Index(index_name))
#return the object 

def get_index(index_name: str): 
    pc_key = keyring.get_password("pinecone-api-key", "dev")
    pc = Pinecone(api_key=pc_key)
    return pc.Index(index_name)
