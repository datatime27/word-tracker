
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

TRANSCRIPTS_DIR = 'transcripts'
CHANNEL_INFO_FILE_NAME = 'channel_info.json'
WORD_FREQUENCY_FILE_NAME = 'word_frequency.json'
BATCH_SIZE = 100

def calc(channel_name):
    print("Calculating",channel_name)
    doc_frequency = defaultdict(int)
    channel_directories = os.listdir(TRANSCRIPTS_DIR)
    total_docs = 0
    for channel_directory in channel_directories:
        filepath = os.path.join(TRANSCRIPTS_DIR, channel_directory, WORD_FREQUENCY_FILE_NAME)
        with open(filepath, 'rb') as f:
            obj = json.load(f)
            for word, word_count in obj['words'].items():
                doc_frequency[word] += 1
            if channel_directory == channel_name:
                term_frequency = obj['words']
                total_words = obj['total_words']
                total_videos = obj['total_videos']
            total_docs += 1
            
    tf_idf = []
    for word, counts in term_frequency.items():
        word_count = counts['word_count']
        video_count = counts['video_count']
        if video_count < 4:
            continue
        if options.videos:
            tf = video_count/total_videos
        else:
            tf = word_count/total_words
        df = doc_frequency[word]/total_docs
        score = tf*log(1/df, 10)
        tf_idf.append((score, word, word_count, video_count, '%.6f' % (tf), doc_frequency[word], '%.6f' % (df)))
  
    tf_idf.sort(reverse=True)
    print("score, word, word count, video count, tf, num docs, df")
    for score, word, word_count, video_count, tf, num_docs, df in tf_idf[:50]:
        print (f"{score}, {word}, {word_count}, {video_count}, {tf}, {num_docs}, {df}")
    print(f"{channel_name} total words: {total_words}")
    print("Total channels:",total_docs)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("--videos",
        action="store_true", dest="videos", default=False,
        help="Use video count instead of word count for Term Frequency.")
    (options, args) = parser.parse_args()
    channel_name = args[0]
    calc(channel_name)
