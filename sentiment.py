import os
import re
import json
import argparse
import time
from pprint import pprint
from openai import OpenAI
import textstat
from multiprocessing import Pool
from collections import defaultdict

DEFAULT_MODEL_NAME = "gpt-3.5-turbo"
DEFAULT_WORD_LIMIT = 500
COMMENTS_FILE_FLUSH_TIME = 600 # secs
SYSTEM_CONTENT = "Please provide the sentiment analysis of this text. Respond with negativity score from 0 to 100: and positivity score from 0 to 100:"

with open('open-ai-key.txt') as f:
    API_KEY = f.read()
client = OpenAI(api_key=API_KEY)


def analyze_chunk(chunk):
    completion = client.chat.completions.create(
      model=DEFAULT_MODEL_NAME,
      temperature=0,
      messages=[
        {"role": "system", "content": SYSTEM_CONTENT},
        {"role": "user", "content": chunk}
      ]
    )
    
    try:
        res = str(completion.choices[0].message.content)
        neg, pos = re.findall('score\\s*:\\s*([\\d]+)', res, flags=re.IGNORECASE)
        neg = float(neg)/100
        pos = float(pos)/100
    except:
        print(chunk)
        print(completion)
        raise
        
    if neg < 0.0 or neg > 1.0 or pos < 0.0 or pos > 1.0:
        print(completion)
        raise Exception('Bad values for chunk')

    return neg, pos
    
def rank_top_excerpts(text):
    system_content = "Please provide the sentiment analysis of this text. Respond with 3 of the most positive excerpts: and 3 of most negative excerpts:"
    completion = client.chat.completions.create(
      model=DEFAULT_MODEL_NAME,
      temperature=0.0,
      messages=[
        {"role": "system", "content": system_content},
        {"role": "user", "content": text}
      ]
    )
    
    try:
        res = str(completion.choices[0].message.content)
        #print(res)
        return res
    except:
        print(text)
        print(completion)
        raise

def analyze_large_texts(texts):
    chunks = []
    words = []
    word_count = 0
    
    for text in texts:
        words += text.split()
        word_count += len(text.split())
        if len(words) > DEFAULT_WORD_LIMIT:
            chunks.append(' '.join(words))
            words = []
            
    chunks.append(' '.join(words))
            
    #print("Num chunks: ",len(chunks))
    #print("Duration: %g min Word Count: %d" % (end_time/60, word_count) )

    sentiment = {'neg': 0.0, 'pos': 0.0}
    chunk_count = 0
    for chunk in chunks:
        try:
            neg, pos = analyze_chunk(chunk)
        except:
            continue
        sentiment['neg'] += neg
        sentiment['pos'] += pos
        chunk_count += 1
        
    if not chunk_count:
        return sentiment
    sentiment['neg'] /= chunk_count
    sentiment['pos'] /= chunk_count
    return sentiment
    


class SentimentAnalyzer:
    def __init__(self, override=False):
        self.override = override


    def processVideoTranscript(self, filepath):
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
            neg, pos = analyze_chunk(chunk)
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
        
    def processComments(self, comments_filepath):
        filename, ext = os.path.splitext(comments_filepath)
        output_filepath = filename + '_sentiment.txt'
        
        existing_dates = set()
        if os.path.exists(output_filepath):
            with open(output_filepath) as f:
                lines = f.readlines()
                for line in lines:
                    if not line.strip():
                        continue
                    date = line.split()[0]
                    existing_dates.add(date)
        else:
            with open(output_filepath,'w') as f:
                f.write('date neg pos\n')

                
        print(existing_dates)
    
        comments_by_date = defaultdict(list)
        dates = set()
        with open(comments_filepath) as f:
            data = json.load(f)

            for comment in data['comments']:
                date = max(comment['publishedAt'],comment['updatedAt'])
                date = date.split('T')[0]
                dates.add(date)
                text = comment['text']
                if not text.endswith('.'):
                    text += '.'
                comments_by_date[date].append(text)
                
        for date in sorted(dates):
            if date in existing_dates:
                continue
            sentiment = analyze_large_texts(comments_by_date[date])
            print(date,sentiment)
            with open(output_filepath,'a') as f:
                f.write('%s %g %g\n' % (date, sentiment['neg'], sentiment['pos']))
            
    def processCommentsExcerpts(self, comments_filepath):
        filename, ext = os.path.splitext(comments_filepath)
        output_filepath = filename + '_excerpts.txt'
            
        comments_by_date = defaultdict(list)
        dates = set()
        with open(comments_filepath) as f:
            data = json.load(f)

            for comment in data['comments']:
                date = max(comment['publishedAt'],comment['updatedAt'])
                date = date.split('T')[0]
                dates.add(date)
                text = comment['text']
                if not text.endswith('.'):
                    text += '.'
                comments_by_date[date].append(text)
                
        for date in sorted(dates):
            try:
                excerpts = rank_top_excerpts('\n'.join(comments_by_date[date]))
                print(date)
                print(excerpts)
                with open(output_filepath,'a') as f:
                    f.write('%s\n%s\n' % (date, excerpts))
            except:
                pass