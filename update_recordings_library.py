import requests
from bs4 import BeautifulSoup
import pickle
import pprint
import ffmpeg
import sys
import os

def update_library(recordings):
    with open(library_filename, 'wb') as library_file:
        pickle.dump(recordings, library_file)


def getEpisodePath(series, season, episode):
    file_string_format = "{}-s{:02}e{:02}"
    seriesDir = series.replace(' ','_').lower()
    seasonDir = "season{:02}".format(season)
    episodeDir = file_string_format.format(seriesDir, season, episode)
    return os.path.join('tablo_library', seriesDir, seasonDir, episodeDir)


def getRecordingSegList(pvr_url, recordingId):
    r = requests.get(pvr_url + recordingId + 'segs/')
    if r.ok:
        seg_soup = BeautifulSoup(r.text, 'html.parser')
        segs  = []
        for link in seg_soup.find_all('a'):
            segs.append(link.get('href'))
        segs.remove('../')
        return segs


def getSegmentUrl(segment):
    return pvr_url + recording['href'] + 'segs/' + segment

def getPlaylistUrl(segment):
    return pvr_url + recording['href'] + 'pl/playlist.m3u8'

pp = pprint.PrettyPrinter(indent=2)
base_url = 'http://192.168.0.215:18080'
pvr_url = base_url + '/pvr/'
library_filename = 'tablo_library.p'

r = requests.get(pvr_url)
soup = BeautifulSoup(r.text, 'html.parser')

recordings = {}
for link in soup.find_all('a'):
    try:
        recording_id = int(link.get('href')[:-1])
        recordings[recording_id] = {'id': recording_id, 'href': link.get('href')}
    except ValueError as e:
        print("Discarding {}".format(link.get('href')))
        pass

updated = False
try:
    with open(library_filename, 'rb') as library_file:
        recordings.update(pickle.load(library_file))
        updated = True
except IOError as e:
    print("Initializing tablo recordings library...")
    pass

update_library(recordings) if updated else None

print("Downloading recording details...")

for recording in recordings.values():
    if 'files' not in recording:
        print("Getting details for {}".format(recording["id"]))
        r = requests.get(pvr_url + recording['href'])
        rec_soup = BeautifulSoup(r.text, 'html.parser')
        files  = []
        for link in rec_soup.find_all('a'):
            files.append(link.get('href'))
        recording['files'] = files

update_library(recordings)

print("Downloading recording metadata...")
updated = False
have_meta = (1 for k in recordings.values() if k.get('meta'))
have_segs = (1 for k in recordings.values() if k.get('segsList'))
print("{}/{} have metadata".format(sum(have_meta),len(recordings)))
print("{}/{} have segment list".format(sum(have_segs),len(recordings)))

for recording in recordings.values():
    if 'meta.txt' in recording['files']:
        if 'meta' not in recording:
            r = requests.get(pvr_url + recording['href'] + 'meta.txt')
            if r.ok:
                updated = True
                recording['meta'] = r.json()
            else:
                print("No meta found for {}".format(recording['href']))
    else:
        print("No meta found for {}".format(recording['href']))
    if 'segs/' in recording['files']:
        if 'segsList' not in recording:
            segsList = getRecordingSegList(pvr_url, recording['href'])
            if segsList:
                updated = True
                recording['segsList'] = segsList

update_library(recordings) if updated else None

count = 0
print("Building library structure...")
for recording in recordings.values():
    if 'meta' in recording:
        meta = recording['meta']
        if 'recSeries' in meta:
            series = meta['recSeries']['jsonForClient']
            seriesName = series['title']
            if 'Big Bang Theory' in seriesName:
                count += 1
                if 'recEpisode' in meta:
                    episode = meta['recEpisode']['jsonForClient']
                    season = episode['seasonNumber']
                    episode = episode['episodeNumber']
                    recording['path'] = getEpisodePath(seriesName, season, episode)
                    if not os.path.exists(recording['path']):
                        os.makedirs(recording['path'])

def download_episode_segments():
    print("Downloading episode segments...")
    #ffmpeg -i http://192.168.0.215:18080/pvr/23309/pl/playlist.m3u8 -c copy episode.mkv
    for recording in recordings.values():
        recording['segsList'].remove('../')
        for seg in recording['segsList']:
            if 'path' in recording:
                print seg
                segsPath = os.path.join(recording['path'], 'segs')
                if not os.path.exists(segsPath):
                    os.makedirs(segsPath)
                segFilePath = os.path.join(segsPath, seg)
                if not os.path.exists(segFilePath):
                    r = requests.get(getSegmentUrl(seg))
                    if r.ok:
                        with open(segFilePath, 'wb') as segFile:
                            segFile.write(r.content)
                            updated = True
        sys.exit() if updated else None

print ("Downloading and converting episodes...")
for recording in recordings.values():
    if 'path' in recording and 'downloaded' not in recording:
        if 'pl/' in recording['files']:
            ffmpeg.input(getPlaylistUrl(recording['id'])).output(recording['path'] + '.mkv', codec='copy').run()
            recording['downloaded'] = True
            update_library(recordings)

print("{} TBBT episodes found".format(count))
