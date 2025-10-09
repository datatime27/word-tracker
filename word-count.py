
# Get the total number of words for a channel

import io
import os
import re
import json
import datetime
import time
import requests
from captions import EXCLUDED_FILE_LIST
from pprint import pprint
from optparse import OptionParser
import google_auth_oauthlib.flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

TRANSCRIPTS_DIR = 'transcripts'
BATCH_SIZE = 100

def count(channel_name):
    directory = os.path.join(TRANSCRIPTS_DIR,channel_name)
    filenames = os.listdir(directory)
    word_counts = {}
    total_counter = 0
    for filename in filenames:
        if filename in EXCLUDED_FILE_LIST:
            continue
        filepath = os.path.join(directory, filename)
            
        with open(filepath, 'rb') as f:
            obj = json.load(f)
            video_id = obj['id']
            counter = 0
            for caption in obj['captions']:
                words = caption['text'].split()
                for word in words:
                    word = re.sub("[\\W]",'',word.lower())
                    if not word:
                        continue
                    counter += 1
            word_counts[video_id] = counter
            total_counter += counter
    #pprint(word_counts)
    print("Total words",total_counter)
                

if __name__ == '__main__':
    parser = OptionParser()
    (options, args) = parser.parse_args()
    channel_name = args[0]
    count(channel_name)

'''
select videos.id, count(1) as word_count
from words join videos ON (words.video_id = videos.id)
join channels ON (videos.channel_id = channels.id)
where channels.name = 'markiplier'
group by 1
having word_count < 1000
order by 1


select channels.name, count(1) as word_count
from words join videos ON (words.video_id = videos.id)
join channels ON (videos.channel_id = channels.id)
group by 1
order by 1
'''