import sys
import captions
from pprint import pprint
from collections import defaultdict
from optparse import OptionParser

#skip_phrases = ('logan','paul','be','bee','bees','baby','pppp','pbbb','blah','no','go','mine','beep','yurm')
skip_phrases = ()
EXCLUDED_VIDEOS = ['MT-CEo_K2cc']
class LongestPhrase(captions.Parser):
    def run(self, directory, phrase_length):
        self.parse(directory)
        phrases = defaultdict(list)
        for videoId, first_word in self.first_word_in_video.items():
            if not first_word:
                continue
            if videoId in EXCLUDED_VIDEOS:
                continue
            #if videoId in('dSDBr0WjrwQ', '97Gh93Daio0', '3TflpIllQHY','BKJy7BFP3Is','b91vrgVY-ZQ','LGzkyNHFMvY'):
            #    continue # skip bee movie, mine video, yurm, blah,logan paul, tom scott
            ref = first_word
            while ref:
                phrase = self.get_phrase(ref, phrase_length)
                if phrase:
                    phrases[phrase].append(ref)
                ref = ref.next_ref
            
        top_phrases = []
        for phrase, refs in phrases.items():
            #if len(refs) < 4:
            #    continue
            top_phrases.append((len(refs),phrase, refs))
            
        top_phrases.sort(reverse=True)
        
        results = []
        for count, phrase, refs in top_phrases[:10]:
            print()
            print(count, phrase)
            for ref in refs[:5]:
                print(ref.title, ref.link)
                results.append(ref)
            
        return results
            
    def get_phrase(self, first_word_of_phrase, phrase_length):
        phrase = []
        ref = first_word_of_phrase
        for i in range(phrase_length):
            phrase.append(ref.word)
            ref = ref.next_ref
            if not ref:
                return None
            
        if phrase[0] in skip_phrases and phrase[-1] in skip_phrases:
            return None
        return ' '.join(phrase) 

if __name__ == '__main__':
    # python longest-phrase.py MrBeast 4
    parser = OptionParser()
    (options, args) = parser.parse_args()
    channel = args[0].strip("'") # MrBeast
    phrase_length = int(args[1]) # 4
    processor = LongestPhrase()
    processor.run(channel , phrase_length)
