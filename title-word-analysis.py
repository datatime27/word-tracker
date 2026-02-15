
# -*- coding: utf-8 -*-

import io
import os
import re
import json
import datetime
import time
from captions import EXCLUDED_FILE_LIST, TRANSCRIPTS_DIR
from math import log
from pprint import pprint
from optparse import OptionParser
from collections import defaultdict
import numpy

BATCH_SIZE = 100

def isShort(obj):
    if len(obj['captions']) == 0:
        return True
    caption = obj['captions'][-1]
    return caption['start'] + caption['duration'] < 60

def add_phrases(words, phrase_length, view_count, phrases):
    for i in range(len(words)-phrase_length+1):
        phrase = ' '.join(words[i:i+phrase_length])
        phrases[phrase].append(view_count)

def calc(channel_name, cuttoff_date=None):
    print("Calculating",channel_name)
    word_map = defaultdict(list)
    length_map = defaultdict(list)
    phrases = defaultdict(list)
    punctuation_map = defaultdict(list)

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
            try:
                view_count = int(obj['stats']['viewCount'])
            except:
                print(f'Cannot read viewCount from {filepath}')
                continue
            title = obj['title']
            words = title.split()
            add_phrases(words, 2, view_count, phrases)
            add_phrases(words, 3, view_count, phrases)
            add_phrases(words, 4, view_count, phrases)
            
            length_map[len(words)].append(view_count)
            if '?' in title:
                punctuation_map['?'].append(view_count)
            if '!' in title:
                punctuation_map['!'].append(view_count)
            if '?' not in title and '!' not in title:
                punctuation_map[' '].append(view_count)
            
            for word in set(words):
                word = re.sub('&#39;s', '', word.lower())
                word = re.sub("[\\W]",'',word)
                if not word:
                    continue

                word_map[word].append(view_count)
            
    word_scores = []
    for word,l in word_map.items():
        if len(l) < 2:
            continue
        word_scores.append((int(numpy.mean(l)), len(l), word))
        
    
    for phrase,l in phrases.items():
        if len(l) < 2:
            continue
        word_scores.append((int(numpy.mean(l)), len(l), phrase))
    
  
    word_scores.sort(reverse=True)
    print('Ave Views; Num of Titles; Phrase')
    for views, titles, phrase in word_scores[:20]:
        print (f'{views}; {titles}; {phrase}')
    print()
    
    title_lengths = []
    for word_count,l in length_map.items():
        title_lengths.append((word_count, int(numpy.mean(l)), len(l)))
    title_lengths.sort()
    print('title length; average view count; num of titles')
    for length, views, titles in title_lengths:
        print (f'{length}; {views}; {titles}')
    print()

    print('punctuation; average view count; num of titles')
    for punctuation,l in punctuation_map.items():
        print(f'{punctuation}; {int(numpy.mean(l))}; {len(l)}')
    print()

if __name__ == '__main__':
    parser = OptionParser()
    (options, args) = parser.parse_args()
    channel_name = args[0]
    cuttoff_date = None
    if len(args) > 1:
        cuttoff_date = args[1]
    calc(channel_name, cuttoff_date)
