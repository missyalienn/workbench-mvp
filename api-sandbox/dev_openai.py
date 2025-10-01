#openai API sandbox

from openai import OpenAI
import os
import keyring
from dotenv import load_dotenv
#load_dotenv()


# Get OpenAI API key from Keychain
api_key = keyring.get_password("openai-key", "dev")

#Initalize OpenAI
client = OpenAI(api_key=api_key)

response = client.responses.create(
    model="gpt-3.5-turbo",
    input="Write a short bedtime story about a unicorn."
)

print(response.output_text)

