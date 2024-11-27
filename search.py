
import sys
import os
import re
import captions
from pprint import pprint
from optparse import OptionParser
   

if __name__ == '__main__':
    parser = OptionParser()
    (options, args) = parser.parse_args()

    channel = args[0]
    p = captions.Parser()
    p.parse(args[0])
    
    words = args[1].lower()
    print (words,':')
    
    if ' ' not in words: # Single word
        for ref in p.findWord(words):
            print(ref.link,ref.text)
        print()
    else: # Phrase
        for ref in p.findWords(words.split()):
            print(ref.link,ref.text)
        print()
    '''
    print ('"feast.*":')
    for words in p.reWord('feast.*'):
        print(words)
    print()
    
    print ('"feastables":')
    for ref in p.findWord('feastables'):
        print(ref.link,ref.text)
    print()
    '''   
    