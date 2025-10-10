#Full Sandbox 

import os
import sys
import keyring
import json
import time
import re
from math import e
import praw
import tiktoken
from openai import OpenAI

#OpenAI Auth + Client
api_key = keyring.get_password("openai-key", "dev")
client = OpenAI(api_key=api_key)

# Load JSONL
with open("reddit_data_small.jsonl", "r", encoding="utf-8") as f:
    records = [json.loads(line) for line in f]

enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
total_tokens = 0

#Loop through all records and get the number of tokens
for record in records:
    text =  record["text"]
    tokens = enc.encode(text)
    token_count = len(tokens)
    total_tokens += token_count

    print(f"{record['id']}: {token_count} tokens")
    print(f"{record['id']}: {text[:100]}...")
    print("\n")

print(f"Total tokens: {total_tokens}")
print(f"Total records: {len(records)}")
print(f"Average tokens per record: {total_tokens / len(records)}")

#Result: Total tokens: 1942
#Total records: 30
#Average tokens per record: 64.73333333333333
