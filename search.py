
import sys
import os
import re
from pprint import pprint
from optparse import OptionParser
from captions import Parser, TRANSCRIPTS_DIR

def getAllChannels():
    return os.listdir(TRANSCRIPTS_DIR)

def search(channel_name, words):
    print (f"{channel_name} {words}:")
    p = Parser()
    p.parse(channel_name)    
    
    if ' ' not in words: # Single word
        results = p.findWord(words)
        for ref in results:
            print(ref.publishedAt, ref.link,ref.text)
        print(len(results), 'results\n')
    else: # Phrase
        results = p.findWords(words.split())
        for ref in results:
            print(ref.publishedAt, ref.link, ref.text)
        print(len(results), 'results\n')

if __name__ == '__main__':
    parser = OptionParser()        
    (options, args) = parser.parse_args()

    channel_name = args[0]
    words = args[1].lower()
    
    if channel_name == 'all':
        for channel_name in getAllChannels():
            search(channel_name, words)
    else:
        search(channel_name, words)
    
