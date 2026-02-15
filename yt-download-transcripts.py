# -*- coding: utf-8 -*-

import io
import os
import re
import json
import datetime
import time
import traceback
import random
import requests
from pprint import pprint
from optparse import OptionParser
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api import TranscriptsDisabled
from youtube_transcript_api import NoTranscriptFound
from youtube_transcript_api import IpBlocked
from youtube_transcript_api import AgeRestricted
from youtube_transcript_api.proxies import WebshareProxyConfig
from captions import TRANSCRIPTS_DIR, CHANNEL_INFO_FILE_NAME,EXCLUDED_FILE_LIST

def getAllChannels():
    channel_names = os.listdir(TRANSCRIPTS_DIR)
    random.shuffle(channel_names)
    return channel_names

def download_channel_info(outputDir, channel_name):
    filepath = os.path.join(outputDir, CHANNEL_INFO_FILE_NAME)
    if not os.path.exists(filepath):
        channel_info = get_channel_info(channel_name)
        write_channel_info(channel_info, outputDir)
        return channel_info
        
    with open(filepath) as f:
        return json.load(f)

def get_channel_info(channel_name):
    url = 'https://www.youtube.com/@'+channel_name 
    r = requests.get(url)
    
    channel_ids = re.findall('channel_id=(.+?)"',r.text)
    if len(channel_ids) == 0:
        raise Exception("Cannot find channel_id for ",url)
                
    imgs = re.findall('<link rel="image_src" href="(.+?)">',r.text)
    if len(imgs) == 0:
        raise Exception("Cannot find channel image for ",url)

    r.close()
    
    return {
        'channel_name': channel_name,
        'channel_id': channel_ids[0],
        'img': imgs[0],
    }

def write_channel_info(channel_info, output_dir):
    filepath = os.path.join(output_dir, CHANNEL_INFO_FILE_NAME)
    with open(filepath, 'w') as f:
        json.dump(channel_info,f,indent=4)
        print("Wrote", filepath)

class TranscriptDownloader:
    def __init__(self):
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
        
    def download_channel_transcripts(self, channel_names):
        for channel_name in channel_names:
            outputDir = os.path.join(TRANSCRIPTS_DIR,channel_name)
            channel_info = download_channel_info(outputDir, channel_name)
            channel_id = channel_info['channel_id']
            
            pending_videos = self.get_pending_videos(outputDir)
            print(f"Channel {channel_name}: found {len(pending_videos)} transcripts to download")
            
            for counter, video in enumerate(pending_videos):
                self.process_video(outputDir, counter, video)
        
    def get_pending_videos(self, outputDir):
        pending_videos = []
        for file in os.listdir(outputDir):
            if file in EXCLUDED_FILE_LIST:
                continue
            with open(os.path.join(outputDir, file)) as f:
                obj = json.load(f)
                if 'captions' in obj:
                    continue
                pending_videos.append(obj)
        
        return pending_videos

    def process_video(self, outputDir, counter, video):
        videoId = video['id']
        publishedAt = video['publishedAt']
        title = video['title']
        filepath = os.path.join(outputDir, videoId+'.json')
       
        try:
            video['captions'] = self.fetch_captions(counter, videoId)
            
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
        except AgeRestricted:
            print(counter, videoId, publishedAt, title.encode('utf-8'), '-- AGE RESTRICTED')
            video['captions'] = []
            video['error'] = 'AgeRestricted'
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
        print(f"Downloading {videoId}")
        transcript = self.ytt_api.fetch(videoId,preserve_formatting=True)
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

    if not args:
        channel_names = getAllChannels()
    else:
        channel_names = args
        
    downloader = TranscriptDownloader()
    downloader.download_channel_transcripts(channel_names)
