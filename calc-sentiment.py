
import os
import sys
import time
from sentiment import SentimentAnalyzer
from optparse import OptionParser

TRANSCRIPTS_DIR = 'transcripts'

def calcSentiment(channel_name):
    directory = os.path.join(TRANSCRIPTS_DIR, channel_name)
    filenames = os.listdir(directory)
    analyzer = SentimentAnalyzer(options.force)
    for index, filename in enumerate(filenames):
        filepath = os.path.join(directory, filename)
        print(index, time.asctime(), filepath)
        result = analyzer.run(filepath)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("--force",
                  action="store_true", dest="force", default=False,
                  help="Redo calc for all videos, even videos that have already been calculated.")
    (options, args) = parser.parse_args()
    channel_name = args[0]
    calcSentiment(channel_name)


