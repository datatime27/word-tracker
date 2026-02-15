import os
import sys
import re
from captions import parseHTML, TRANSCRIPTS_DIR, PHRASE_FREQUENCY_FILE_NAME, EXCLUDED_FILE_LIST
import json
import copy
import traceback
from pprint import pprint
from collections import defaultdict
from optparse import OptionParser
import concurrent.futures

MAX_PHRASE_LENGTH = 20
MAX_WORKERS = 12
MIN_PHRASE_COUNT = 4

def getAllChannels():
    return os.listdir(TRANSCRIPTS_DIR)
    
def get_phrases(words):
    curr_phrase = []
    phrases_list = []
    for word in words:
        curr_phrase.append(word.encode('cp850', errors='replace').decode('cp850'))
        if len(curr_phrase) >= 2:
            phrases_list.append(' '.join(curr_phrase))
        
    return phrases_list 

def readWordsFromFile(filepath):
    with open(filepath, 'rb') as f:
        obj = json.load(f)
        words = []
        if 'captions' not in obj:
            return words
            
        for caption in obj['captions']:
            segments = parseHTML(caption['text'])
            # Skip weird color coding used on Jet Lag used on Nebula Ad Read.
            if len(segments) > 6:
                continue
            for html,text in segments:
                for word in text.split():
                    word = re.sub("[\\W]",'',word.lower())
                    if not word:
                        continue
                    words.append(word)
    return words

def processFile(filepath):
    phrases = defaultdict(int)
    words = readWordsFromFile(filepath)
    if not words:
        return phrases, 0
            
    for word_index in range(len(words)-1):
        curr_phrase = []
        for word in words[word_index:word_index+MAX_PHRASE_LENGTH]:
            curr_phrase.append(word.encode('cp850', errors='replace').decode('cp850'))
            if len(curr_phrase) >= 2:
                phrase = ' '.join(curr_phrase)
                phrases[phrase] += 1
    return (phrases, len(words))

def updateChannel(channel_name):
    directory = os.path.join(TRANSCRIPTS_DIR,channel_name)
    filenames = os.listdir(directory)
    
    filepaths = []
    for filename in filenames:
        if filename in EXCLUDED_FILE_LIST:
            continue            
        filepaths.append(os.path.join(directory, filename))
        
    phrases = defaultdict(int)
    total_videos = 0
    total_words = 0
    #for filepath in filepaths:
    #        (result, word_count) = processFile(filepath)
    with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = executor.map(processFile, filepaths)
        for (result, word_count) in results:
            total_words += word_count
            for phrase, count in result.items():
                phrases[phrase] += count
            print(f"Processed {channel_name} {total_videos} of {len(filenames)} files {len(phrases):,} phrases")
            total_videos += 1
    
    top_phrases = {}
    for phrase, count in phrases.items():
        if count < MIN_PHRASE_COUNT:
            continue
        top_phrases[phrase] = count
        
    obj = {
        'total_keys': len(phrases),
        'total_words': total_words,
        'total_videos': total_videos,
        'phrases': top_phrases,
        }

    filepath = os.path.join(TRANSCRIPTS_DIR, channel_name, PHRASE_FREQUENCY_FILE_NAME)
    with open(filepath, 'w') as f:
        ret = json.dump(obj,f,indent=4, sort_keys=True)
    print(f"Updated: {channel_name}, Total phrases: {len(top_phrases)}")
       

def shouldProcessChannel(channel_name):
    directory = os.path.join(TRANSCRIPTS_DIR,channel_name)
    filenames = os.listdir(directory)
    
    latest_modtime = 0
    phrase_frequency_modtime = 0
    for filename in filenames:
        filepath = os.path.join(directory, filename)
        if filename == PHRASE_FREQUENCY_FILE_NAME:
            phrase_frequency_modtime = os.path.getmtime(filepath)
            continue
        if filename in EXCLUDED_FILE_LIST:
            continue
        latest_modtime = max(latest_modtime, os.path.getmtime(filepath))
        
    # Phrase Frequency file is more recent than every transcript file
    if phrase_frequency_modtime > latest_modtime:
        print (f"{channel_name} {len(filenames)} files - already up to date")
        return False
    return True
        
def processChannel(channel_name):
    try:
        if not options.force and not shouldProcessChannel(channel_name):
                return
        updateChannel(channel_name)
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
        
    for channel_name in channel_names:
        if channel_name in EXCLUDED_FILE_LIST:
            continue
        processChannel(channel_name)