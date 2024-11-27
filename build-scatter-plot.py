
import sys
from captions import Parser
from pprint import pprint
from collections import defaultdict


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

channel = sys.argv[1]
p = Parser()
p.parse(channel, cut_off_date='2000-01-01')

sentiment_by_year = defaultdict(list)

print("# Raw Scatter Plot:")
print("videoId;title;words-per-min;viewCount;publishedAt;negative;positive")
for videoId, first_ref in p.first_word_in_video.items():
    ref = first_ref
    year = int(ref.publishedAt.split('-')[0])
    word_counter = 0
    end = 0
    text = []
    while ref:
        word_counter += 1
        end = ref.start + ref.duration
        text.append(ref.word)

        ref = ref.next_ref
        
    rate = word_counter/(end/60.0)
    stats = p.video_stats[videoId]
    sentiment = getSentiment(p.sentiment[videoId]['time_series'])
    sentiment_by_year[year].append(sentiment)
    print ('%s;%s;%.2f;%s;%s;%g;%g' % (videoId, first_ref.title, rate, stats['viewCount'], first_ref.publishedAt, sentiment['neg'], sentiment['pos']))
    #print '%s: %d words %.2f min %.2f words/min views: %s' % (videoId, word_counter, end/60.0, rate, stats)

print()
print("# Year over Year sentiment:")
print("year negative positive")
for year,sentiments in sorted(sentiment_by_year.items()):
    sentiment = getSentiment(sentiments)
    print ('%s %g %g' % (year, sentiment['neg'], sentiment['pos']) )
