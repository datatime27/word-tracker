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
import google_auth_oauthlib.flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/youtube.force-ssl',
    'https://www.googleapis.com/auth/youtubepartner-channel-audit',
    ]

API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'
CLIENT_SECRETS_FILE = 'client_secret.json' # Add your youtube api client login file here.

TRANSCRIPTS_DIR = 'transcripts'
CHANNEL_INFO_FILE_NAME = 'channel_info.json'

def prepare_dir(channel_name):
    if not os.path.exists(TRANSCRIPTS_DIR):
        os.mkdir(TRANSCRIPTS_DIR)
        
    outputDir = os.path.join(TRANSCRIPTS_DIR,channel_name)
    if not os.path.exists(outputDir):
        os.mkdir(outputDir)
    return outputDir

def download_channel_info(channel_name):
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


class YoutubeConnection:
    def __init__(self,channel_id, output_dir):
        self.api = self.get_service()
        self.channel_id = channel_id
        self.output_dir = output_dir

    def get_service(self):
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CLIENT_SECRETS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        try:
            return build(API_SERVICE_NAME, API_VERSION, credentials = creds)

        except HttpError as err:
            print(err)
            
    def find_oldest_transcript(self):
        print("Finding oldest transcript...")
        oldest_timestamp = datetime.datetime.now()
        for filename in os.listdir(self.output_dir):
        
            if filename == CHANNEL_INFO_FILE_NAME:
                continue
            filepath = os.path.join(self.output_dir, filename)
            if os.path.isdir(filepath):
                continue
            with open(filepath, 'rb') as f:
                obj = json.load(f)
                timestamp = datetime.datetime.strptime(obj['publishedAt'],'%Y-%m-%dT%H:%M:%SZ')
                oldest_timestamp = min(oldest_timestamp,timestamp)
                
        print(f"Searching before {oldest_timestamp}")
        return oldest_timestamp

    def download_channel_transcripts(self):
        if options.resume:
            publishedBefore = self.find_oldest_transcript() - datetime.timedelta(seconds=1)
        else:
            publishedBefore = datetime.datetime.now() + datetime.timedelta(days=1)

        #publishedBefore = datetime.datetime(2018,8,5)
        print("Searching from",publishedBefore)
        
        # For whatever reason, sometimes YouTube drops videos, so we set publishedAfter
        # to mitigate that.
        publishedAfter =  publishedBefore - datetime.timedelta(days=365)
        
        publishedBefore = publishedBefore.isoformat()+'Z'
        publishedAfter = publishedAfter.isoformat()+'Z'
        counter = 0
        while True:
            search_results = self.api.search().list(
                part="snippet",
                type="video",
                channelId=self.channel_id,
                order='date',
                maxResults=50,
                publishedAfter=publishedAfter,
                publishedBefore=publishedBefore).execute()
            for search_result in search_results['items']:
                publishedBefore=search_result['snippet']['publishedAt']
                publishedBefore = datetime.datetime.strptime(publishedBefore,'%Y-%m-%dT%H:%M:%SZ') - datetime.timedelta(seconds=1)
                publishedAfter =  publishedBefore - datetime.timedelta(days=365)
                publishedBefore = publishedBefore.isoformat()+'Z'
                publishedAfter = publishedAfter.isoformat()+'Z'
                metadata = self.api.videos().list(
                    id=search_result['id']['videoId'],
                    part="snippet,statistics",
                ).execute()['items'][0]
                
                already_downloaded = self.process_video(counter,search_result,metadata)
                if already_downloaded:
                    # Keep going to check that all videos are downloaded.
                    if options.check_all or options.update: 
                        continue
                    # Stop: we've now downloaded all new vidoes since last download.
                    else: 
                        return
                time.sleep(0.001)
                counter+=1
            # Youtube pagination is broken - search_results['nextPageToken'] doesn't work
            # So we have to end this way instead
            if not search_results['items']:
                break
                
    def process_video(self, counter, item, metadata):
        videoId = str(item['id']['videoId'])
        title =  item['snippet']['title']
        publishedAt = item['snippet']['publishedAt']
        img = item['snippet']['thumbnails']['default']['url']
        stats = metadata['statistics']
        description = metadata["snippet"]['description']
        
        filepath = os.path.join(self.output_dir, videoId+'.json')
        if os.path.exists(filepath):
            # Load file, update stats, write it back out
            if options.update:
                if 'viewCount' not in stats:
                    print(f'Cannot update {videoId} - There is no viewCount on YouTube')
                    return True
                with open(filepath, 'r', encoding='utf-8') as f:
                    obj = json.load(f)
                    
                obj['title'] = title
                obj['img'] = img
                obj['stats'] = stats
                obj['description'] = description
                
                with open(filepath, 'w') as f:
                    json.dump(obj,f,indent=4)
                print(filepath + ' updated')
                return True

            # We are all caught up
            else:
                print(filepath + ' already exists')
                return True
        
        obj = {
            'id': videoId,
            'title': title,
            'publishedAt': publishedAt,
            'img': img,
            'stats': stats,
            'description': description,
        }

        with open(filepath, 'w') as f:
            json.dump(obj,f,indent=4)
            print(counter, videoId, publishedAt, title.encode('utf-8'))
        return False
 
if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("--all",
                  action="store_true", dest="check_all", default=False,
                  help="Check that all videos have been downloaded - Default will only download new videos.")
    parser.add_option("--update",
                  action="store_true", dest="update", default=False,
                  help="Download all videos but only update their stats.")
    parser.add_option("--resume",
                  action="store_true", dest="resume", default=False,
                  help="Resume download from where we last left off.")
    (options, args) = parser.parse_args()
    channel_name = args[0]
    
    channel_info = download_channel_info(channel_name)
    output_dir = prepare_dir(channel_name)
    write_channel_info(channel_info, output_dir)
    client = YoutubeConnection(channel_info['channel_id'],output_dir)
    client.download_channel_transcripts()
