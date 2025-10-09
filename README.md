
PLEASE NOTE THIS CODE IS PRETTY HACKY AND MAY NOT WORK OUT OF THE BOX.

# Word Tracker

Requirements to download transcripts:

* Set up Account with YouTube API Client 
https://developers.google.com/youtube/v3/quickstart/python

* Install YouTubeTranscriptApi and create Webshare Account
** Please don't skip the section on how to create a Webshare account **
https://pypi.org/project/youtube-transcript-api/

* Create file to save WebShare credentials: "web-share-key.json"
```
{
"username": "PROVIDED BY WEBSHARE",
"password": "PROVIDED BY WEBSHARE"
}
```

1. Download the metadata for all of the videos on a YouTube channel.
2. Then download all transcripts for that channel (and any other channels in your directories)
```
> python yt-download-video-stats.py DataTime27
> python yt-download-transcripts.py
```

This will open up a website and walk you through the process to give access to the script.
At some point it might say this is unsafe, but you'll have to accept it in order for the script to work.

Once it runs, it should generate your new directory with a .json file for every video in the channel named by its video id.
The .json files will initially just contain metadata. Once you run `yt-download-transcripts.py` then they will be filled with caption data.

Then you can run various processes on it:
```
> python build-overview.py DataTime27
> python build-scatter-plot.py DataTime27
> python search.py DataTime27 "but enough talk"
```
