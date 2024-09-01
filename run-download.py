# -*- coding: utf-8 -*-

import io
import os
import re
import json
import datetime
import time
import requests
from pprint import pprint
from optparse import OptionParser
import google_auth_oauthlib.flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from youtube_transcript_api import YouTubeTranscriptApi,TranscriptsDisabled,NoTranscriptFound

SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/youtube.force-ssl',
    'https://www.googleapis.com/auth/youtubepartner-channel-audit',
    ]

API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'
CLIENT_SECRETS_FILE = 'client_secret.json' # Add your youtube api client login file here.

TRANSCRIPTS_DIR = 'transcripts'

def prepare_dir(channel_name):
    if not os.path.exists(TRANSCRIPTS_DIR):
        os.mkdir(TRANSCRIPTS_DIR)
        
    outputDir = os.path.join(TRANSCRIPTS_DIR,channel_name)
    if not os.path.exists(outputDir):
        os.mkdir(outputDir)
    return outputDir

def get_channel_id(channel_name):
    url = 'https://www.youtube.com/@'+channel_name 
    r = requests.get(url)
    
    channelIDs = re.findall('channel_id=(.+?)"',r.text)
    if len(channelIDs) == 0:
        raise Exception("Cannot find channel_id for ",url)
    r.close()
    return channelIDs[0]


class YoutubeConnection:
    def __init__(self,channelID, outputDir):
        self.api = self.get_service()
        self.channelID = channelID
        self.outputDir = outputDir
        
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

    def download_channel_transcripts(self):
        publishedBefore = datetime.datetime.now() + datetime.timedelta(days=1)
        publishedBefore = publishedBefore.isoformat()+'Z'
        counter = 0
        while True:
            search_results = self.api.search().list(
                part="snippet",
                type="video",
                channelId=channelID,
                order='date',
                maxResults=50,
                publishedBefore=publishedBefore).execute()
            for search_result in search_results['items']:
                publishedBefore=search_result['snippet']['publishedAt']
                publishedBefore = datetime.datetime.strptime(publishedBefore,'%Y-%m-%dT%H:%M:%SZ') - datetime.timedelta(seconds=1)
                publishedBefore = publishedBefore.isoformat()+'Z'
                stats = self.api.videos().list(
                    id=search_result['id']['videoId'],
                    part="snippet,statistics",
                ).execute()['items'][0]['statistics']
                already_downloaded = self.download_transcripts(counter,search_result,stats)
                if already_downloaded:
                    if options.check_all: # Keep going to check that all videos are downloaded.
                        continue
                    else: # Stop: we've now downloaded all new vidoes since last download.
                        return
                time.sleep(0.001)
                counter+=1
            # Youtube pagination is broken - search_results['nextPageToken'] doesn't work
            # So we have to end this way instead
            if not search_results['items']:
                break

    def download_transcripts(self, counter, item, stats):
        videoId = str(item['id']['videoId'])
        title =  item['snippet']['title']
        publishedAt = item['snippet']['publishedAt']
        filepath = os.path.join(self.outputDir, videoId+'.json')
        # We are all caught up
        if os.path.exists(filepath):
            print(filepath + ' already exists')
            return True
        
        try:
            srt = YouTubeTranscriptApi.get_transcript(videoId,languages=['en', 'en-US'])
            obj = {
                'id': videoId,
                'title': title,
                'publishedAt': publishedAt,
                'captions': srt,
                'stats': stats,
            }

            with open(filepath, 'w') as f:
                json.dump(obj,f,indent=4)
                print(counter, videoId, publishedAt, title.encode('utf-8'))
        except TranscriptsDisabled:
            print(counter, videoId, publishedAt, title.encode('utf-8'), '-- NO CAPTIONS')
            pass
        except NoTranscriptFound:
            print(counter, videoId, publishedAt, title.encode('utf-8'), '-- NO CAPTIONS')
            pass
        except:
            print(counter, videoId, publishedAt, title.encode('utf-8'), '-- UNKNOWN ERROR')
            pass
            
        return False

 
if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("--check_all",
                  action="store_true", dest="check_all", default=False,
                  help="Check that all videos have been downloaded - Default will only download new videos.")
    (options, args) = parser.parse_args()
    channel_name = args[0]
    
    channelID = get_channel_id(channel_name)
    outputDir = prepare_dir(channel_name)
    client = YoutubeConnection(channelID,outputDir)
    client.download_channel_transcripts()
