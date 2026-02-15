
# -*- coding: utf-8 -*-

import io
import os
import re
import json
import datetime
import time
from math import log
from pprint import pprint
from optparse import OptionParser
from collections import defaultdict
from captions import TRANSCRIPTS_DIR, CHANNEL_INFO_FILE_NAME, PHRASE_FREQUENCY_FILE_NAME

NO_MATCH = 0
PREFER_FIRST = 1
PREFER_SECOND = 2
MAX_PRINTOUT = 100

def compare_strings(a, b):
    if a in b:
        return PREFER_SECOND
    elif b in a:
        return PREFER_FIRST
    else:
        return NO_MATCH
    
def is_phrase_repeated(phrase, previous_phrases):
    for previous_phrase in previous_phrases:
        if phrase in previous_phrase:
            return True
        if previous_phrase in phrase:
            return True
    return False
    
def calc(channel_name):
    print("Calculating",channel_name)
    doc_frequency = defaultdict(int)
    channel_directories = os.listdir(TRANSCRIPTS_DIR)
    total_docs = 0
    for channel_directory in channel_directories:
        filepath = os.path.join(TRANSCRIPTS_DIR, channel_directory, PHRASE_FREQUENCY_FILE_NAME)
        if not os.path.exists(filepath):
            continue
        with open(filepath, 'rb') as f:
            obj = json.load(f)
            if 'phrases' not in obj:
                continue
            for phrase, phrase_count in obj['phrases'].items():
                doc_frequency[phrase] += 1
            if channel_directory == channel_name:
                term_frequency = obj['phrases']
                print(len(term_frequency))
                total_keys = obj['total_keys']
                total_videos = obj['total_videos']
            total_docs += 1
            
    tf_idf = []
    for phrase, phrase_count in term_frequency.items():
        tf = phrase_count/total_keys
        df = doc_frequency[phrase]/total_docs
        score = tf*log(1/df, 10)
        tf_idf.append((score, phrase, phrase_count, '%.6f' % (tf), doc_frequency[phrase], '%.6f' % (df)))
  
    tf_idf.sort(reverse=True)
    previous_phrases = []
    print("score, is_repeat, phrase, phrase_count, tf, num docs, df")
    for score, phrase, phrase_count, tf, num_docs, df in tf_idf[:MAX_PRINTOUT]:
        is_repeat = is_phrase_repeated(phrase, previous_phrases)
        print (f'{score}, {is_repeat}, "{phrase}", {phrase_count}, {tf}, {num_docs}, {df}')
        previous_phrases.append(phrase)
        
    # Find specific phrase if possible
    if options.phrase:
        for index, (score, phrase, phrase_count, tf, num_docs, df) in enumerate(tf_idf):
            if phrase == options.phrase:
                print (f"Index: {index} is {score}, '{phrase}', {phrase_count}, {tf}, {num_docs}, {df}")

    print(f"{channel_name} total_keys: {total_keys}")
    print("Total channels:",total_docs)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("--phrase",
        dest="phrase", default=None,
        help="Look for this specific phrase.")
    (options, args) = parser.parse_args()
    channel_name = args[0]
    calc(channel_name)
