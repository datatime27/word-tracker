# -*- coding: utf-8 -*-

import io
import os
import re
import json
import datetime
import time
import traceback
import requests
from pprint import pprint
from optparse import OptionParser
from youtube_transcript_api import YouTubeTranscriptApi,TranscriptsDisabled,NoTranscriptFound,IpBlocked
from youtube_transcript_api.proxies import WebshareProxyConfig


TRANSCRIPTS_DIR = 'transcripts'
CHANNEL_INFO_FILE_NAME = 'channel_info.json'

WORD_FREQUENCY_FILE_NAME = 'word_frequency.json'
EXCLUDED_FILES = [CHANNEL_INFO_FILE_NAME, WORD_FREQUENCY_FILE_NAME]

def get_channel_info(outputDir):
    filepath = os.path.join(outputDir, CHANNEL_INFO_FILE_NAME)
    with open(filepath) as f:
        return json.load(f)

class TranscriptDownloader:
    def __init__(self,channel_id, outputDir):
        self.channel_id = channel_id
        self.outputDir = outputDir
        self.ytt_api = self.getYTTAPI()

    def getYTTAPI(self):
        with open('web-share-key.json', 'r') as f:
            login = json.load(f)
            return YouTubeTranscriptApi(
                proxy_config=WebshareProxyConfig(
                    proxy_username=login['username'],
                    proxy_password=login['password'],
                )
            )

    def download_channel_transcripts(self):
        pending_videos = self.get_pending_videos()
        print("Found {} transcripts to download".format(len(pending_videos)))
        
        for counter, video in enumerate(pending_videos):
            self.process_video(counter,video)
        
    def get_pending_videos(self):
        pending_videos = []
        for file in os.listdir(self.outputDir):
            if file in EXCLUDED_FILES:
                continue
            with open(os.path.join(self.outputDir, file)) as f:
                obj = json.load(f)
                if 'captions' in obj:
                    continue
                pending_videos.append(obj)
        
        return pending_videos

    def process_video(self, counter, video):
        videoId = video['id']
        publishedAt = video['publishedAt']
        title = video['title']
        filepath = os.path.join(self.outputDir, videoId+'.json')
       
        try:
            video['captions'] = self.fetch_captions(counter,videoId)
            with open(filepath, 'w') as f:
                json.dump(video,f,indent=4)
                print(counter, videoId, publishedAt, title.encode('utf-8'))
                
        except (TranscriptsDisabled, NoTranscriptFound):
            print(counter, videoId, publishedAt, title.encode('utf-8'), '-- NO CAPTIONS')
            video['captions'] = []
            with open(filepath, 'w') as f:
                json.dump(video,f,indent=4)
                print(counter, videoId, publishedAt, title.encode('utf-8'))
            pass
        except IpBlocked:
            print(counter, videoId, publishedAt, title.encode('utf-8'), '-- IP BLOCKED')
            traceback.print_exc()
            raise
        except:
            print(counter, videoId, publishedAt, title.encode('utf-8'), '-- UNKNOWN ERROR')
            traceback.print_exc()
            pass

    def fetch_captions(self, counter, videoId):
        captions = []
        #srt = YouTubeTranscriptApi.get_transcript(videoId,languages=['en', 'en-US'])
        transcript = self.ytt_api.fetch(videoId)
        for segment in transcript:
            captions.append({
                'text': segment.text,
                'start': segment.start,
                'duration': segment.duration})
        return captions
 
if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("--check-all",
                  action="store_true", dest="check_all", default=False,
                  help="Check that all videos have been downloaded - Default will only download new videos.")
    parser.add_option("--resume",
                  action="store_true", dest="resume", default=False,
                  help="Resume download from where we last left off.")
    (options, args) = parser.parse_args()
    channel_name = args[0]
    
    outputDir = os.path.join(TRANSCRIPTS_DIR,channel_name)
    channel_info = get_channel_info(outputDir)
    client = TranscriptDownloader(channel_info['channel_id'],outputDir)
    client.download_channel_transcripts()
