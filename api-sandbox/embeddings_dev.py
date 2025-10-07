#Embeddings Dev Sandbox


from openai import OpenAI
import os
import keyring
import json
from dotenv import load_dotenv

load_dotenv()

api_key = keyring.get_password("openai-key", "dev")
client = OpenAI(api_key=api_key)

#Get Embeddings 
response = client.embeddings.create(
    input="Your text string goes here",
    model="text-embedding-3-small"
)

#print(response.data[0].embedding)
#prints the embedding list as a list of floats 

# Convert the response object to a dictionary
response_dict = response.to_dict()

# Trim the embeddings list to 3 elements 
for item in response_dict["data"]:
    item["embedding"] = item["embedding"][:3]

# Print the response object formatted as JSON (trimmmed) 
print(json.dumps(response_dict, indent=2))



