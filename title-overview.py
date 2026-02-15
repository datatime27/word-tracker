
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
            try:
                view_count = int(obj['stats']['viewCount'])
            except:
                print(f'Cannot read viewCount from {filepath}')
                continue
            try:
                last_caption = obj['captions'][-1]
            except:
                print(f'Cannot read captions from {filepath}')
                continue
                
            end_secs = int(last_caption['start'] + last_caption['duration'])
            minutes, seconds = divmod(end_secs, 60)
            runtime = f'{minutes}:{seconds:02d}'

            videoId = obj['id']
            title = obj['title']
            titles.append((obj['publishedAt'], str(view_count), runtime, videoId, title))
        
    titles.sort(reverse=True)
    print('Date    Views    Runtime    VideoId    Title')
    for i in titles:
        print('    '.join(i))
    print()
if __name__ == '__main__':
    parser = OptionParser()
    (options, args) = parser.parse_args()
    channel_name = args[0]
    cuttoff_date = None
    if len(args) > 1:
        cuttoff_date = args[1]
    calc(channel_name, cuttoff_date)
