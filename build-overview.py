
import sys
import re
import json
from captions import Parser
from pprint import pprint
from collections import defaultdict
from statistics import mean,stdev
from textstat.textstat import textstatistics
from optparse import OptionParser

def percent(value):
    return '%.2f%%' % (value*100)

def print_table(table):
    for total, name in reversed(table):
        print(name,total)
        
words_to_match = ()

def getSentiment(time_series):
    sentiment = {'neg': 0.0, 'pos': 0.0}
    if not time_series:
        return sentiment
    for i in time_series:
        sentiment['neg'] += i['neg']
        sentiment['pos'] += i['pos']
        
    sentiment['neg'] /= len(time_series)
    sentiment['pos'] /= len(time_series)
    return sentiment

def print_word_popularity(words_dict, size, total_words):
    all_words_table = []
    non_dictionary_words_table = []
    difficult_words_table = []
    single_use_word_count = 0
    single_use_big_words = []
    match_words_count = []
    histogram_of_syllables = defaultdict(int)
    textstats = textstatistics()
    profanity = []
    profanity_count = 0
    easy_word_count = 0
    difficult_word_count = 0
    
    for word, refs in words_dict.items():
        # Don't count numbers as words
        if re.search('^\\d+$',word):
            continue
            
        if word in words_to_match:
            match_words_count.append((len(refs), word))
            
        #Histogram of syllable in the dictionary
        if refs[0].is_in_dictionary:
            syllables = textstats.syllable_count(word)
            frequency_used = len(refs)
            histogram_of_syllables[syllables] += frequency_used
            
            if textstats.is_difficult_word(word):
                difficult_words_table.append((len(refs), word))
                difficult_word_count +=1
            else:
                easy_word_count += 1
            
        # Find the number of words in the dictionary used only once
        if len(refs) == 1 and refs[0].is_in_dictionary:
            single_use_word_count += 1
            if len(word) > 6:
                single_use_big_words.append((len(word), word))
            
        # Find most common words not in dictionary (proper nouns)
        if not refs[0].is_in_dictionary:
            non_dictionary_words_table.append((len(refs), word))
            
        # Find most common words
        all_words_table.append((len(refs), word))
        
        if word in ('ass','dumbass','jackass','__') or re.search('(shit)|(fuck)', word):
            profanity.append((len(refs), word))
            profanity_count += len(refs)

    all_words_table.sort()
    non_dictionary_words_table.sort()
    difficult_words_table.sort()
    match_words_count.sort()
    single_use_big_words.sort()
    profanity.sort()
    
    print('Most common words:')
    print_table(all_words_table[-size:])
    print()

    print('Most common words not in dictionary (proper nouns):')
    print_table(non_dictionary_words_table[-size:])
    print()

    print('Most common words in dictionary but not easy words:')
    print_table(difficult_words_table[-size:])
    print()

    print('Most common match words:')
    print_table(match_words_count)
    print()
    
    print('Number of words in dictionary spoken only once',single_use_word_count)
    print()
    
    print('Biggest words in dictionary spoken only once:')
    print_table(single_use_big_words[-size:])
    print()
    
    print('Histogram of syllables of word vs frequency used:')
    total = sum(histogram_of_syllables.values())
    print('Total:', total)
    for key in sorted(histogram_of_syllables.keys()):
        value = histogram_of_syllables[key]
        print (key, value, percent(value/total))
    print()
    
    print('Known easy words used:', easy_word_count)
    print('Known difficult words used:', difficult_word_count)
    print('Percentage of difficult words used:', percent(difficult_word_count/(easy_word_count+difficult_word_count)))
    print()
    
    print('Profanity:')
    print('Total:', profanity_count)
    if profanity_count:
        print('Which is 1 out of', int(total_words/profanity_count))
    pprint(profanity)
    print()
    
    
if __name__ == '__main__':
    parser = OptionParser()
    (options, args) = parser.parse_args()
    channel_name = args[0]

    p = Parser()
    p.parse(channel_name, cut_off_date='2000-01-01')
    #p.parse('mrbeast',cut_off_date='2000-01-01')
    words_per_year = defaultdict(int)
    duration_per_year = defaultdict(int)
    shorts_per_year = defaultdict(int)
    videos_per_year = defaultdict(int)
    rates_per_year = defaultdict(list)
    best_videos_per_year = {}
    sentiment_by_year = defaultdict(list)
    years = set()
    lexicon = set()
    longest_words = defaultdict(list)
    for videoId, first_ref in p.first_word_in_video.items():
        ref = first_ref
        word_counter = 0
        end = 0
        final_start = 0
        year = int(ref.publishedAt.split('-')[0])
        years.add(year)
        videos_per_year[year] += 1
        viewCount = int(p.video_stats[videoId]['viewCount'])
        if year not in best_videos_per_year or best_videos_per_year[year]['viewCount'] < viewCount:
            best_videos_per_year[year] = {'videoId' : videoId, 'viewCount':  viewCount}
        while ref:
            word_counter += 1
            words_per_year[year] += 1
            if ref.is_in_dictionary:
                lexicon.add(ref.word)
                if len(ref.word) > 6:
                    longest_words[len(ref.word)].append(ref.word+' '+ref.link)
            end = ref.start + ref.duration
            final_start = max(final_start, ref.start)
            ref = ref.next_ref

        rate = word_counter/(end/60.0)
        rates_per_year[year].append(rate)
        #print '%s: %d words %.2f min %.2f words/min' % (videoId, word_counter, end/60.0, rate)
        duration_per_year[year] += end
        if final_start < 60:
            shorts_per_year[year] += 1
        sentiment_by_year[year].append(getSentiment(p.sentiment[videoId]['time_series']))

    total_words = 0
    total_duration = 0
    total_videos = 0

    print ('year, total videos, shorts, total words, total hrs, speaking rate (avg words/min), speaking rate (stddev), '+
        'best_video, best_video (views), neg, pos')

    for year in sorted(years):
        total_words += words_per_year[year]
        total_duration += duration_per_year[year]
        total_videos += videos_per_year[year]
        
        rate = words_per_year[year]/(duration_per_year[year]/60.0)
        sentiment = getSentiment(sentiment_by_year[year])
        print ('%d, %d, %d, %d, %.2f, %.2f, %.2f, %s, %d, %g, %g' % (
            year, videos_per_year[year], shorts_per_year[year], words_per_year[year], duration_per_year[year]/3600.0, mean(rates_per_year[year]), 
            stdev(rates_per_year[year]), best_videos_per_year[year]['videoId'], best_videos_per_year[year]['viewCount'], 
            sentiment['neg'], sentiment['pos']))
    print()
    print('Total words:',total_words)
    print('Total duration: %.2f hrs' % (total_duration/3600.0) )
    print('Total videos:',total_videos)

    print ('lexicon_count:',len(lexicon))
    longest_length = sorted(longest_words.keys())[-1]
    print ('longest word length:',longest_length)
    print ('longest words:')
    pprint(longest_words[longest_length])
    print()

    print_word_popularity(p.word_index, 10,total_words=total_words)
