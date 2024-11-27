
import os
import sys
import time
from sentiment import SentimentAnalyzer
from optparse import OptionParser

COMMENTS_DIR = 'comments'

def calcSentiment(videoId):
    filepath = os.path.join(COMMENTS_DIR, videoId) + '.json'
    analyzer = SentimentAnalyzer()
    #result = analyzer.processComments(filepath)
    result = analyzer.processCommentsExcerpts(filepath)

if __name__ == '__main__':
    parser = OptionParser()
    (options, args) = parser.parse_args()
    videoId = args[0].strip("'")
    print(repr(videoId))
    calcSentiment(videoId)


