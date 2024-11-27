
import os
import sys
import time
import json
from optparse import OptionParser
from collections import defaultdict

COMMENTS_DIR = 'comments'

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

def plotSentiment(commentId):
    dates = set()
    sentiment_by_day = defaultdict(list)

    filepath = os.path.join(COMMENTS_DIR, commentId) + '.json'
    with open(filepath) as f:
        data = json.load(f)
    
    for comment in data['comments']:
        if 'sentiment' not in comment:
            continue
        date = comment['updatedAt'].split('T')[0]
        dates.add(date)
        sentiment_by_day[date].append(comment['sentiment'])
        
    print('date, neg, pos')
    for date in sorted(dates):
        sentiment = getSentiment(sentiment_by_day[date])
        print(date, sentiment['neg'], sentiment['pos'])
    
if __name__ == '__main__':
    parser = OptionParser()
    (options, args) = parser.parse_args()
    commentId = args[0]
    plotSentiment(commentId)


