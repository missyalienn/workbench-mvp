import os 
import keyring

from pinecone import Pinecone

#Connect to pinecone and create client 
pc_key = keyring.get_password("pinecone-api-key", "dev")
pc = Pinecone(api_key=pc_key)

#Create index handle 
index_name = "workbench-mvp"
index = pc.Index(index_name)

