# -*- coding: utf-8 -*-

import io
import os
import os.path
import pickle
import json
import re
from datetime import datetime
from pprint import pprint
import google_auth_oauthlib.flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from optparse import OptionParser

SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/youtube.force-ssl',
    'https://www.googleapis.com/auth/youtubepartner',
    ]
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

API_SERVICE_NAME = 'youtubeAnalytics'
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'
CLIENT_SECRETS_FILE = 'client_secret.json' # Add your youtube api client login file here.

COMMENTS_DIR = 'comments'

def prepare_dir():
    if not os.path.exists(COMMENTS_DIR):
        os.mkdir(COMMENTS_DIR)

def authorName(input):
    s = input
    s = re.sub('[^A-Za-z0-9_\\-]', ' ', s)
    s = s.strip()
    s = s.replace(' ', '_')
    return s

class GetYoutubeComments:
    def __init__(self, videoId):
        self.api = self.get_service()
        self.videoId = videoId
        self.counter = 0
        self.results = {'videoId': videoId, 'comments':[]}
        
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
    

    def get_comment_threads(self, pageToken=None):
        response = self.api.commentThreads().list(
            part='id,snippet,replies',
            videoId=self.videoId,
            pageToken=pageToken,
            maxResults=100,
            ).execute()
        for item in response['items']:
            self.counter += 1
            name = authorName(item['snippet']['topLevelComment']['snippet']['authorDisplayName'])
            '''
            print ('----------------------------------')
            print ('Author: %s (%s) (%s)' %(name, repr(item['snippet']['topLevelComment']['snippet']['authorDisplayName']), item['id']))
            print (item['snippet']['topLevelComment']['snippet']['updatedAt'])
            print ('Text:', item['snippet']['topLevelComment']['snippet']['textDisplay'])
            '''
            self.results['comments'].append({
                'id': item['id'],
                'author': name,
                'publishedAt':item['snippet']['topLevelComment']['snippet']['publishedAt'],
                'updatedAt': item['snippet']['topLevelComment']['snippet']['updatedAt'],
                'text': item['snippet']['topLevelComment']['snippet']['textDisplay'],
                })
            if 'replies' in item:
                totalReplyCount = item['snippet']['totalReplyCount']
                if totalReplyCount == len(item['replies']['comments']):
                    #print ('Replies:')
                    for reply in item['replies']['comments']:
                        self.counter += 1                            
                        '''
                        print ('\tReply:', reply['id'])
                        print ('\tAuthor:', authorName(reply['snippet']['authorDisplayName']))
                        print ('\t', reply['snippet']['updatedAt'])
                        print ('\tText:', reply['snippet']['textDisplay'])
                        print()
                        '''
                        self.results['comments'].append({
                            'id': reply['id'],
                            'author': authorName(reply['snippet']['authorDisplayName']),
                            'publishedAt': reply['snippet']['publishedAt'],
                            'updatedAt': reply['snippet']['updatedAt'],
                            'topCommentId': item['id'],
                            'text': reply['snippet']['textDisplay'],
                            })
                else:
                    self.get_large_comment_replies(item['id'])
        print ('%d comment threads' % (client.counter))

        #if response['pageInfo']['resultsPerPage'] == response['pageInfo']['totalResults']:
        if 'nextPageToken' in response:
            try:
                self.get_comment_threads(response['nextPageToken'])
            except:
                print(response['pageInfo'])
                raise
                
        
    def get_large_comment_replies(self, parentId, pageToken=None):
        response = self.api.comments().list(
            part='id,snippet',
            parentId=parentId,
            pageToken=pageToken,
            maxResults=100,
            ).execute()
            
        for item in response['items']:
            self.counter += 1
            name = authorName(item['snippet']['authorDisplayName'])
            self.results['comments'].append({
                'id': item['id'],
                'author': name,
                'publishedAt':item['snippet']['publishedAt'],
                'updatedAt': item['snippet']['updatedAt'],
                'text': item['snippet']['textDisplay'],
                })
        if 'nextPageToken' in response:
            self.get_large_comment_replies(parentId,pageToken=response['nextPageToken'])

    def write(self, videoId):
        filepath = os.path.join(COMMENTS_DIR, videoId) + '.json'
        with open(filepath, 'w') as f:
            json.dump(self.results,f,indent=4)

if __name__ == '__main__':
    parser = OptionParser()
    (options, args) = parser.parse_args()
    videoId = args[0].strip("'")
    
    print(repr(videoId))
    prepare_dir()
    client = GetYoutubeComments(videoId)
    client.get_comment_threads()
    client.write(videoId)
    #print 
    #print ('%d comment threads' % (client.counter))
    