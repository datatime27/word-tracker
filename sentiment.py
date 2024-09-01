import os
import re
import json
import argparse
import time
from pprint import pprint
from openai import OpenAI
import textstat

DEFAULT_MODEL_NAME = "gpt-3.5-turbo"
DEFAULT_WORD_LIMIT = 500
SYSTEM_CONTENT = "Please provide the sentiment analysis of this text. Respond with negativity score from 0 to 100: and positivity score from 0 to 100:"

with open('open-ai-key.txt') as f:
    API_KEY = f.read()
client = OpenAI(api_key=API_KEY)

class SentimentAnalyzer:
    def __init__(self, override=False):
        self.override = override

    def analyze_chunk(self, chunk):
        completion = client.chat.completions.create(
          model=DEFAULT_MODEL_NAME,
          messages=[
            {"role": "system", "content": SYSTEM_CONTENT},
            {"role": "user", "content": chunk}
          ]
        )
        
        try:
            res = str(completion.choices[0].message.content)
            neg, pos = re.findall('score\s*:\s*([\\d]+)', res, flags=re.IGNORECASE)
            neg = float(neg)/100
            pos = float(pos)/100
        except:
            print(completion)
            raise
            
        if neg < 0.0 or neg > 1.0 or pos < 0.0 or pos > 1.0:
            print(completion)
            raise Exception('Bad values for chunk')

        return neg, pos

    def run(self, filepath):
        with open(filepath) as f:
            data = json.load(f)

        if not self.override and 'sentiment' in data:
            print ('Already processed',filepath)
            return

        chunks = []
        words = []
        word_count = 0
        start_time = None
        end_time = None
        for caption in data['captions']:
            if not start_time:
                start_time = caption['start']
            words += caption['text'].split()
            word_count += len(caption['text'].split())
            if len(words) > DEFAULT_WORD_LIMIT:
                chunks.append((start_time,' '.join(words)))
                words = []
                start_time = None
            end_time = caption['start'] + caption['duration']
                
        if len(words) > 5:
            chunks.append((start_time,' '.join(words)))
        
        if word_count < 5:
            print("Not enough words to process")
            return
            
        #print("Num chunks: ",len(chunks))
        #print("Duration: %g min Word Count: %d" % (end_time/60, word_count) )
    
        time_series = []
        for start_time, chunk in chunks:
            neg, pos = self.analyze_chunk(chunk)
            #print(start_time, neg, pos)
            time_series.append({
                "start_time": start_time, 
                "neg": neg, 
                "pos": pos,
                })
                
        data["sentiment"] = {
            "model": DEFAULT_MODEL_NAME,
            "time_series": time_series
            }
            
        with open(filepath, 'w') as f:
            json.dump(data,f,indent=4)
        
