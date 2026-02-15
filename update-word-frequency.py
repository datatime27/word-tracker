
# -*- coding: utf-8 -*-

import io
import os
import re
import json
import datetime
import time
from captions import parseHTML, TRANSCRIPTS_DIR, WORD_FREQUENCY_FILE_NAME, EXCLUDED_FILE_LIST
from pprint import pprint
from optparse import OptionParser
from collections import defaultdict
import concurrent.futures
import traceback

MAX_WORKERS = 8

def getAllChannels():
    return os.listdir(TRANSCRIPTS_DIR)

def update(channel_name):
    try:
        directory = os.path.join(TRANSCRIPTS_DIR,channel_name)
        filenames = os.listdir(directory)
        word_frequency = defaultdict(lambda: defaultdict(int))
        
        filepaths = []
        latest_modtime = 0
        word_frequency_modtime = 0
        for filename in filenames:
            filepath = os.path.join(directory, filename)
            if filename == WORD_FREQUENCY_FILE_NAME:
                word_frequency_modtime = os.path.getmtime(filepath)
                continue
            if filename in EXCLUDED_FILE_LIST:
                continue
            latest_modtime = max(latest_modtime, os.path.getmtime(filepath))
            filepaths.append(filepath)
            
        # Word Frequency file is more recent than every transcript file
        if not options.force and word_frequency_modtime > latest_modtime:
            print (f"{channel_name} already up to date")
            return
            
        total_words = 0
        total_videos = 0
        for filepath in filepaths:
            with open(filepath, 'rb') as f:
                obj = json.load(f)
                words_set = set()
                total_videos += 1
                if 'captions' not in obj:
                    continue
                for caption in obj['captions']:
                    segments = parseHTML(caption['text'])
                    for html,text in segments:
                        for word in text.split():
                            word = re.sub("[\\W]",'',word.lower())
                            if not word:
                                continue
                            words_set.add(word)
                            word_frequency[word]['word_count'] += 1
                            total_words += 1
                    
                for word in words_set:
                    word = re.sub("[\\W]",'',word.lower())
                    if not word:
                        continue
                    word_frequency[word]['video_count'] += 1

        filepath = os.path.join(directory, WORD_FREQUENCY_FILE_NAME)
        obj = {
            'total_keys': len(word_frequency),
            'total_words': total_words,
            'total_videos': total_videos,
            'words': word_frequency,
            }
        with open(filepath, 'w') as f:
            ret = json.dump(obj,f,indent=4, sort_keys=True)
        print(f"Updated: {channel_name}, Total words: {total_words}, Total Videos: {total_videos}")
    except:
        print("An error occurred:")
        traceback.print_exc()

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("--force",
        action="store_true", dest="force", default=False,
        help="Force update despite mod time.")

    (options, args) = parser.parse_args()
    if not args:
        channel_names = getAllChannels()
    else:
        channel_names = args
        
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = executor.map(update, channel_names)
