import requests
import pickle
import pprint
import ffmpeg
import os


pp = pprint.PrettyPrinter(indent=2)
base_url = 'http://192.168.0.215'
rest_server = base_url + ':8885'
http_server = base_url + ':18080'
recordings_url = rest_server + '/recordings'
pvr_url = http_server + '/pvr/'
library_filename = 'tablo_library.p'
recording_repository = '/Volumes/Multimedia/TvShows'


def update_library(recordings):
    with open(library_filename, 'wb') as library_file:
        pickle.dump(recordings, library_file)


def getEpisodePath(series, season, episode):
    file_string_format = "{} - s{:02}e{:02}"
    seriesDir = series
    seasonDir = "Season {:02}".format(season)
    episodeDir = file_string_format.format(seriesDir, season, episode)
    return os.path.join(seriesDir, seasonDir, episodeDir)


def getTabloRipperEpisodePath(series, season, episode, title):
    episodeDir = getEpisodePath(series, season, episode)

    if title is not None:
        title = title.replace('/','')
        episodeDir += (' - ' + title)
    return episodeDir


def getPlaylistUrl(recording_id):
    return pvr_url + recording_id + '/pl/playlist.m3u8'


def has_recording_been_downloaded(recording_repository, recording_path):
    return os.path.exists(os.path.join(recording_repository, recording_path))

def find_downloaded_recordings():
    for recording in recordings.values():
        if recording.get('path') is not None and recording.get('downloaded', False) == False:
            recording['downloaded'] = has_recording_been_downloaded(recording_repository, (recording['path'] + '.mp4'))
            if recording['downloaded']:
                print("Found recording for {}".format(recording['path']))

def download_and_convert_tv_episode(recording):
    print("Archiving {} -- {}".format(recording['id'], recording['path']))
    episodeDir = (os.path.dirname(os.path.join(recording_repository, recording['path'])))
    if not os.path.exists(episodeDir):
        os.makedirs(episodeDir)
    ffmpeg.input(getPlaylistUrl(recording['id'])).output(os.path.join(recording_repository, recording['path'] + '.mp4'), absf='aac_adtstoasc', codec='copy').run()
    recording['downloaded'] = True

shows = ['Modern Family', 'Big Bang Theory', 'NOVA', 'Nature']
def download_and_convert_episodes():
    count = 0
    print ("Downloading and converting episodes...")
    for recording in recordings.values():
        if recording.get('path') is not None and recording.get('downloaded', False) == False:
            if any(show in recording['path'] for show in shows):
                download_and_convert_tv_episode(recording)
                update_library(recordings)
                count += 1

    print("Retrieved {} episodes".format(count))

def initialize_recordings():
    r = requests.get(recordings_url + '/airings')
    r.raise_for_status()
    recordings = {}
    for item in r.json():
        recording_id = os.path.basename(item)
        recordings[recording_id] = {'id': recording_id, 'uri': item}
    return recordings

def get_recording_metadata(recording_uri):
    r = requests.get(rest_server + recording['uri'])
    r.raise_for_status()
    return r.json()

def update_recording_metadata(recording):
    recording['meta'] = get_recording_metadata(recording['uri'])
    recording['status'] = recording['meta'].get('video_details', {}).get('state')


def get_recording_path(meta):
    if 'episode' in meta:
        episode = meta['episode']
        seriesName = meta['airing_details']['show_title']
        season = episode['season_number']
        episodeNum = episode['number']
        title = episode.get('title')
        return getTabloRipperEpisodePath(seriesName, season, episodeNum, title)


def update_recording_path(recording):
    recording['path'] = get_recording_path(recording['meta'])


recordings = initialize_recordings()

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
downloaded = (1 for k in recordings.values() if k.get('downloaded', False) == True)
print("{}/{} have metadata".format(sum(have_meta), len(recordings)))
print("{}/{} recordings downloaded".format(sum(downloaded), len(recordings)))


print("Downloading recording details...")
for recording in recordings.values():
    if 'meta' not in recording:
        update_recording_metadata(recording)
        updated = True

update_library(recordings) if updated else None

print("Building library structure...")
for recording in recordings.values():
    if 'meta' in recording and recording['status'] == 'finished':
            update_recording_path(recording)
            updated = True

update_library(recordings) if updated else None

find_downloaded_recordings()
update_library(recordings)
download_and_convert_episodes()

print("Done")
