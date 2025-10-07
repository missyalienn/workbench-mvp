#Full Sandbox 

import os
import sys
import keyring
import json
import time
import re
from math import e
from dotenv import load_dotenv

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
text = records[0]["text"] #Get the text of the first record
tokens = enc.encode(text)
print(len(tokens))  # number of tokens




#enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
#text = "Sand first, then prime."
#tokens = enc.encode(text)
#print(len(tokens))  # number of tokens
