
import sys
import os
import re
from pprint import pprint
from optparse import OptionParser
from concurrent.futures import ProcessPoolExecutor, as_completed
from captions import Parser, TRANSCRIPTS_DIR

HTML_TEMPLATE = 'search-results-template.html'
MAX_WORKERS = 12

def getAllChannels():
    return os.listdir(TRANSCRIPTS_DIR)

def search(channel_name, search_inputs, after=None, before=None):
    p = Parser()
    p.parse(channel_name)
    
    final_results = []
    for search_input in search_inputs:
        search_input = search_input.lower()
        if ' ' not in search_input:  # Single word
            results = p.findWord(search_input)
        else:  # Phrase
            results = p.findWords(search_input.split())

        # Filter by date range
        if after or before:
            filtered = []
            for ref in results:
                if after and ref.publishedAt < after:
                    continue
                if before and ref.publishedAt > before:
                    continue
                filtered.append(ref)
            results = filtered

        final_results += [[ref.publishedAt, ref.title, ref.deformatted_text, ref.start, ref.videoId, ref.link] for ref in results]
    return final_results
    
def printResults(channel_name, phrases, results, htmlPath):
    
    html_items = []
    for (publishedAt, title, text, start_time, videoId, link) in results:
        print(f"{publishedAt} {link} {text} ")
        html_items.append([
            str(publishedAt),
            title.decode("utf-8"),
            text,
            getTimecode(start_time), 
            getImgAnchor(link,f"https://i.ytimg.com/vi/{videoId}/default.jpg")])
        
    print(f"{channel_name} {phrases} ({len(results)} results):")
    if not htmlPath:
        return

    params = {
        'phrases': str(phrases).strip('[]'),
        'num_results': len(html_items),
        'results': str(html_items),
    }
    with open(HTML_TEMPLATE) as f:
        html = f.read() % params
    with open(htmlPath, 'w') as f:
        f.write(html)

def getImgAnchor(href, img):
    return '''<div class="container">
      <img height=64 src="%s" class="image" />
      <div class="overlay">
        <a target="_blank" href="%s" class="icon" >
          <i class="fa fa-play"></i>
        </a>
      </div>
    </div>''' % (img,href)

def getTimecode(t):
    minutes = int(t) / 60
    seconds = int(t) % 60
    timecode = '%02d:%02d' % (minutes, seconds)
    return timecode
    
    
if __name__ == '__main__':
    parser = OptionParser()        
    parser.add_option("--after", dest="after", help="Only include videos published after this date (YYYY-MM-DD)")
    parser.add_option("--before", dest="before", help="Only include videos published before this date (YYYY-MM-DD)")
    parser.add_option("--html", dest=None, help="save output as HTML file")
    (options, args) = parser.parse_args()
    
    if len(args) < 2:
        parser.error("Usage: script.py <channel_name> <words> [--after YYYY-MM-DD] [--before YYYY-MM-DD]")

    channel_name = args[0]
    search_inputs = args[1:]
    
    if channel_name == 'all':
        channels = getAllChannels()
        print(f"Running {len(channels)} channels in parallel...\n")

        # Adjust max_workers depending on your CPU or I/O performance
        with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(search, ch, search_inputs, options.after, options.before): ch
                for ch in channels
            }

            for future in as_completed(futures):
                ch = futures[future]
                try:
                    results = future.result()
                    printResults(channel_name, search_inputs, results, options.html)
                except Exception as e:
                    print(f"Error in {ch}: {e}\n")
    else:
        results = search(channel_name, search_inputs, after=options.after, before=options.before)
        printResults(channel_name, search_inputs, results, options.html)

