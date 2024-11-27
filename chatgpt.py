# Import dependencies
from openai import OpenAI

import json
import time

TEXT = '''One thing that I found frustrating, 
is that the AI doesn’t always give the same answer for the same text. 
If I ask it to process a piece of text multiple times, 
I will sometimes get slightly different answers for the same piece of text. 
Unfortunately, I think this is actually by design since LLMs are designed 
to reply to you like a person would, which means they vary what they say.
'''

with open('open-ai-key.txt') as f:
    API_KEY = f.read()
client = OpenAI(api_key=API_KEY)

completion = client.chat.completions.create(
  model="gpt-3.5-turbo",
  messages=[
    {"role": "system", "content": "Please provide the sentiment analysis of this text. Respond with negativity score from 0 to 100: and positivity score from 0 to 100:"},
    {"role": "user", "content": TEXT}
  ]
)

print(str(completion.choices[0].message.content))


