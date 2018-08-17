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


def getEpisodePath(series, season, episode, title):
    title = title.replace('/','')
    file_string_format = "{} - s{:02}e{:02}"
    seriesDir = series
    seasonDir = "Season {:02}".format(season)
    episodeDir = file_string_format.format(seriesDir, season, episode)
    episodeDir += ' - ' + title if title is not None else None
    return os.path.join(seriesDir, seasonDir, episodeDir)


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
    return pvr_url + recording['id'] + '/segs/' + segment

def getPlaylistUrl(recording_id):
    return pvr_url + recording_id + '/pl/playlist.m3u8'


pp = pprint.PrettyPrinter(indent=2)
base_url = 'http://192.168.0.215'
rest_server = base_url + ':8885'
http_server = base_url + ':18080'
recordings_url = rest_server + '/recordings'
pvr_url = http_server + '/pvr/'
library_filename = 'tablo_library.p'

r = requests.get(recordings_url + '/airings')
r.raise_for_status()
recordings = {}
for item in r.json():
    recording_id = os.path.basename(item)
    recordings[recording_id] = {'id': recording_id, 'uri': item}

try:
    with open(library_filename, 'rb') as library_file:
        recordings.update(pickle.load(library_file))
except IOError as e:
    print("Initializing tablo recordings library...")
    pass

update_library(recordings)

print("Downloading recording metadata...")
updated = False
have_meta = (1 for k in recordings.values() if k.get('meta'))
print("{}/{} have metadata".format(sum(have_meta),len(recordings)))

for recording in recordings.values():
    if 'meta' not in recording:
        r = requests.get(rest_server + recording['uri'])
        r.raise_for_status()
        recording['meta'] = r.json()
        updated = True
    recording['status'] = recording['meta'].get('video_details', {}).get('state')

update_library(recordings) if updated else None

print("Downloading recording details...")

for recording in recordings.values():
    if 'files' not in recording and recording['status'] == 'finished':
        print("Getting details for {}".format(recording["id"]))
        r = requests.get(pvr_url + recording['id'])
        r.raise_for_status()
        rec_soup = BeautifulSoup(r.text, 'html.parser')
        files  = []
        for link in rec_soup.find_all('a'):
            files.append(link.get('href'))
        recording['files'] = files

update_library(recordings)

count = 0
print("Building library structure...")
for recording in recordings.values():
    if 'meta' in recording and recording['status'] == 'finished':
        meta = recording['meta']
        if 'episode' in meta:
            episode = meta['episode']
            seriesName = meta['airing_details']['show_title']
            if 'Big Bang Theory' in seriesName:
                count += 1
                season = episode['season_number']
                episodeNum = episode['number']
                title = episode.get('title')
                recording['path'] = getEpisodePath(seriesName, season, episodeNum, title)
                #if not os.path.exists(recording['path']):
                #    os.makedirs(recording['path'])


def find_downloaded_recordings():
    for recording in recordings.values():
        if 'path' in recording and recording.get('downloaded', False ) == False:
            if os.path.exists(os.path.join('/Volumes/Multimedia/TvShows', (recording['path'] + '.mp4'))):
                print("Found recording for {}".format(recording['path']))
                recording['downloaded'] = True


def download_and_convert_episodes():
    print ("Downloading and converting episodes...")
    for recording in recordings.values():
        if 'path' in recording and recording.get('downloaded', False) == False:
            if 'pl/' in recording['files']:
                print("Archiving {} -- {}".format(recording['id'], recording['path']))
                ffmpeg.input(getPlaylistUrl(recording['id'])).output(os.path.join('/Volumes/Multimedia/TvShows', recording['path'] + '.mp4'), absf='aac_adtstoasc', codec='copy').run()
                recording['downloaded'] = True
                update_library(recordings)

find_downloaded_recordings()
update_library(recordings)
download_and_convert_episodes()
print("{} TBBT episodes found".format(count))
