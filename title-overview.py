
# List all video titles sorted by view count

import io
import os
import re
import json
import datetime
import time
from captions import TRANSCRIPTS_DIR, EXCLUDED_FILE_LIST
from math import log
from pprint import pprint
from optparse import OptionParser
from collections import defaultdict
import numpy

BATCH_SIZE = 100

def isShort(obj):
    caption = obj['captions'][-1]
    return caption['start'] + caption['duration'] < 61

def add_phrases(words, phrase_length, view_count, phrases):
    for i in range(len(words)-phrase_length+1):
        phrase = ' '.join(words[i:i+phrase_length])
        phrases[phrase].append(view_count)

def calc(channel_name, cuttoff_date=None):
    print("Calculating",channel_name)
    titles = []

    for filename in os.listdir(os.path.join(TRANSCRIPTS_DIR,channel_name)):
        if filename in EXCLUDED_FILE_LIST:
            continue
        filepath = os.path.join(TRANSCRIPTS_DIR,channel_name,filename)
        with open(filepath, 'rb') as f:
            obj = json.load(f)
            if cuttoff_date and obj['publishedAt'] < cuttoff_date:
                continue
            if isShort(obj):
                continue
            view_count = int(obj['stats']['viewCount'])
            title = obj['title']
            titles.append((view_count,title))
            
    titles.sort(reverse=True)
    print('Views, title')
    for i in titles[:20]:
        print(*i)
    print()
    for i in titles[-20:]:
        print(*i)

if __name__ == '__main__':
    parser = OptionParser()
    (options, args) = parser.parse_args()
    channel_name = args[0]
    cuttoff_date = None
    if len(args) > 1:
        cuttoff_date = args[1]
    calc(channel_name, cuttoff_date)
