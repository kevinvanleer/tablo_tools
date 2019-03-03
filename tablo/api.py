import requests
import pickle
import ffmpeg
import os

base_url = 'http://192.168.0.215'
rest_server = base_url + ':8885'
http_server = base_url + ':18080'
recordings_url = rest_server + '/recordings'
pvr_url = http_server + '/pvr/'


class DownloadError(Exception):
    pass


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

def find_downloaded_recordings(recordings, recording_repository):
    for recording in recordings.values():
        if recording.get('path') is not None and recording.get('downloaded', False) == False:
            recording['downloaded'] = has_recording_been_downloaded(recording_repository, (recording['path'] + '.mp4'))
            if recording['downloaded']:
                print("Found recording for {}".format(recording['path']).encode('utf-8'))

def download_and_convert_tv_episode(recording, recording_repository):
    print("Archiving {} -- {}".format(recording['id'], recording['path']).encode('utf-8'))
    episodeDir = (os.path.dirname(os.path.join(recording_repository, recording['path'])))
    if not os.path.exists(episodeDir):
        os.makedirs(episodeDir)
    try:
        ffmpeg.input(getPlaylistUrl(recording['id'])).output(os.path.join(recording_repository, recording['path'] + '.mp4'), absf='aac_adtstoasc', codec='copy').run()
        if recording['error']:
            recording['error'] = False
        recording['downloaded'] = True
    except ffmpeg.Error as e:
        r = requests.get(getPlaylistUrl(recording['id']))
        if r.status_code != requests.codes.ok:
            print("Request to Tablo server failed: {}".format(r.status_code))
            recording['error'] = True
            if r.status_code == 404:
                print("Recording {} not found".format(recording['id']))
                recording['status'] = 'not_found'
            elif r.status_code < 500:
                print("Invalid request: {}".format(getPlaylistUrl(recording['id'])));
            elif r.status_code >= 500:
                print("Server error: {}".format(r.status_code))
            else:
                print("Unknown HTTP error: {}".format(r.status_code))
            raise DownloadError('HTTP error', r)
        else:
            raise DownloadError('Unknown ffmpeg error', e)


def initialize_recordings():
    r = requests.get(recordings_url + '/airings')
    r.raise_for_status()
    recordings = {}
    for item in r.json():
        recording_id = os.path.basename(item)
        recordings[recording_id] = {'id': recording_id, 'uri': item}
    return recordings

def get_recording_metadata(recording_uri):
    r = requests.get(rest_server + recording_uri)
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


