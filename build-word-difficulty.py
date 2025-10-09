
import sys
import re
import json
from captions import Parser
from pprint import pprint
from collections import defaultdict
from statistics import mean,stdev
from textstat.textstat import textstatistics
from optparse import OptionParser
    
textstats = textstatistics()

if __name__ == '__main__':
    parser = OptionParser()
    (options, args) = parser.parse_args()
    channel_name = args[0]

    p = Parser()
    p.parse(channel_name, cut_off_date='2000-01-01')
    
    difficult_word_counter = 0
    word_counter = 0
    for videoId, first_ref in p.first_word_in_video.items():
        if not first_ref: continue
        ref = first_ref
        while ref:
            word_counter += 1
            if textstats.is_difficult_word(ref.word):
                difficult_word_counter +=1
            ref = ref.next_ref


    print(f"difficult {difficult_word_counter}/{word_counter} {difficult_word_counter/word_counter}")
            