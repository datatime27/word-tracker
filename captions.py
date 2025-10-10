
import sys
import os
import re
import json
from collections import defaultdict
from pprint import pprint

PUNCTUATION_RE = re.compile('[-;,.\'\"\\!\\?,]')
DICTIONARY_FILE = 'words_dictionary.json'
TRANSCRIPTS_DIR = 'transcripts'
CHANNEL_INFO_FILE_NAME = 'channel_info.json'
WORD_FREQUENCY_FILE_NAME = 'word_frequency.json'
PHRASE_FREQUENCY_FILE_NAME = 'phrase_frequency.json'
EXCLUDED_FILE_LIST = [
    CHANNEL_INFO_FILE_NAME,
    WORD_FREQUENCY_FILE_NAME,
    PHRASE_FREQUENCY_FILE_NAME]

with open(DICTIONARY_FILE) as f:
    WORDS_DICTIONARY = json.load(f)

class WordRef:
    def __init__(self):
        self.word = None
        self.start = None
        self.duration = None
        self.text = None
        self.videoId = None
        self.title = None
        self.publishedAt = None
        self.prev_ref = None
        self.next_ref = None
        self.link = None
        self.last_in_sentence = False

    def __str__(self):
        return self.__repr__()
    def __repr__(self):
        return str({
            'word': self.word,
            'start': self.start,
            'duration': self.duration,
            'text' : self.text,
            'videoId' : self.videoId,
            'title' : self.title,
            'publishedAt' : self.publishedAt,
            'link': self.link,
            'last_in_sentence': self.last_in_sentence,
            })

def buildIndex(videoId, title, publishedAt, captions):
    prev_ref = None
    first_word_in_video = None
    word_index = defaultdict(list)
    for caption in captions:
        text = caption['text']
        #text = re.sub('\\[.+?\\]','',text) # remove non spoken notation
        #text = re.sub('\\*.+?\\*','',text) # remove non spoken notation
        words = text.split()
        
        for word in words:
            last_in_sentence = False
            if re.search(PUNCTUATION_RE, word):
                last_in_sentence = True
                
            word = re.sub("[\\W]",'',word.lower())
            if not word:
                continue
            ref = WordRef()
                    
            ref.word = word
            ref.start = caption['start']
            ref.duration = caption['duration']
            ref.text = caption['text']
            ref.videoId = videoId
            ref.title = title
            ref.publishedAt = publishedAt
            ref.prev_ref = prev_ref
            ref.link = 'https://www.youtube.com/watch?v=%s&t=%ds' % (videoId, caption['start'])
            ref.last_in_sentence = last_in_sentence
            ref.is_in_dictionary = word in WORDS_DICTIONARY
            
            if prev_ref:
                prev_ref.next_ref = ref
            
            else: # first ref for this video
                first_word_in_video = ref
            
            word_index[word].append(ref)
            prev_ref = ref   
            
    return first_word_in_video, word_index

def parseFile(filepath, cut_off_date):
    with open(filepath, 'rb') as f:
        obj = json.load(f)
        title = obj['title'].replace('&#39;',"'").encode('utf-8')
        publishedAt = obj['publishedAt']
        if cut_off_date and publishedAt < cut_off_date:
            return {}
        
        if 'captions' not in obj:
            return {}
            
        videoId = obj['id']
        captions = obj['captions']
        stats = obj['stats']
        sentiment = {'time_series':[]}
        if 'sentiment' in obj:
            sentiment = obj['sentiment']
            
        first_word_in_video, word_index = buildIndex(videoId, title, publishedAt, captions)

        return dict(
            videoId=videoId, 
            captions=captions, 
            stats=stats, 
            sentiment=sentiment, 
            first_word_in_video=first_word_in_video, 
            word_index=word_index,
            )

class Parser:        
    def __init__(self):
        self.word_index = defaultdict(list)
        self.first_word_in_video = {}
        self.video_lengths = []
        self.video_counter = 0
        self.video_stats = {}
        self.sentiment = {}
        self.total_caption_time_secs = 0.0
    
    def parse(self, channel, cut_off_date=None):
        directory = os.path.join(TRANSCRIPTS_DIR, channel)
        filenames = os.listdir(directory)
        print(f"Parsing {len(filenames)} videos")

        for filename in filenames:
            if filename in EXCLUDED_FILE_LIST:
                continue
            filepath = os.path.join(directory, filename)
            
            try:                
                results = parseFile(filepath, cut_off_date)
                if not results:
                    continue
                    
                videoId = results['videoId']
                self.first_word_in_video[videoId] = results['first_word_in_video']
                    
                #merge dictionaries
                for word, refs in results['word_index'].items():
                    self.word_index[word] += refs
                    
                self.video_stats[videoId] = results['stats']
                if 'viewCount' not in self.video_stats[videoId]:
                    self.video_stats[videoId]['viewCount'] = 0
                self.sentiment[videoId] = results['sentiment']
                
                if len(results['captions']) > 10:
                    length = results['captions'][-1]['start'] + results['captions'][-1]['duration']
                    self.video_lengths.append((length,videoId))
                    
                self.video_counter += 1
            except:
                print('Unable to read file:', filepath)
                raise
            
        self.video_lengths.sort()
    

        
    # Search for an exact word and return all references
    def findWord(self, word):
        if word not in self.word_index:
            print ("'%s' not found" % (word))
            return []
            
        return sorted(self.word_index[word], key=lambda x: x.publishedAt, reverse=True)
    
    # Expand regex pattern into all of the words that match it
    def reWord(self, pattern):
        results = {}
        p = re.compile(pattern)
        for word, refs in self.word_index.items():
            if re.search(p,word):
                results[word] = len(refs)
        return results

    # Search for an exact phrase and return all references
    # only_last_in_sentence only works with transcripts that have punctuation 
    def findWords(self, words, only_last_in_sentence=False):
        first_word = words[0].lower()
        if first_word not in self.word_index:
            print ("'%s' not found" % (first_word))
            return []
            
        matches = {}
        refs = self.word_index[first_word]
        for ref in refs:
            if self.matchNextWords(ref, words[1:], only_last_in_sentence):
                id = (ref.videoId,ref.start)
                matches[id] = ref
                
        return list(matches.values())
        
    def matchNextWords(self, ref, words, only_last_in_sentence):
        for word in words:
            word = word.lower()
            if ref.next_ref == None or ref.next_ref.word != word:
                return False
            ref = ref.next_ref
            
        # If we don't care about only finding the phrase at the end of a sentence then return true.
        if not only_last_in_sentence: 
            return True
        
        # We only want the phrase if it occurs at the end of a sentence.
        return ref == None or ref.last_in_sentence
        