
import os
import sys
import time
import json
from optparse import OptionParser
from collections import defaultdict

COMMENTS_DIR = 'comments'

def getDates(commentId):
    num_comments_by_date = defaultdict(int)
    num_comment_words_by_date = defaultdict(int)
    days = set()

    filepath = os.path.join(COMMENTS_DIR, commentId) + '.json'
    with open(filepath) as f:
        data = json.load(f)
        

        for comment in data['comments']:
            day = max(comment['publishedAt'],comment['updatedAt'])
            day = day.split('T')[0]
            days.add(day)
            num_comments_by_date[day] += 1
            num_comment_words_by_date[day] += len(comment['text'].split())
            
    for day in sorted(days):
        print(day, num_comments_by_date[day], num_comment_words_by_date[day])
    print (len(days), 'days total')
if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("--force",
                  action="store_true", dest="force", default=False,
                  help="Redo calc for all commments, even commments that have already been calculated.")
    (options, args) = parser.parse_args()
    commentId = args[0]
    getDates(commentId)


