import argparse
import tablo.api
import tablo.library
import os
import sys
import pickle
import pprint
import requests

import logging

# create logger
logger = logging.getLogger('tablo_util')
logger.setLevel(logging.INFO)

# create console handler and set level to debug
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

pp = pprint.PrettyPrinter(indent=2)
default_recording_repository = '/Volumes/Multimedia/TvShows'

def shouldArchiveAiring(recording):
    return recording.get('path') is not None and recording.get('downloaded', False) == False and recording.get('status', 'new') != 'not_found' and recording.get('duplicate', False) == False

def download_and_convert_episodes(recordings, recording_repository, seriesList):
    count = 0
    logger.info("Downloading and converting episodes...")
    for recording in recordings.values():
        if shouldArchiveAiring(recording):
            if any(show in recording['path'] for show in seriesList):
                try:
                    tablo.api.download_and_convert_tv_episode(recording, recording_repository)
                    count += 1
                except tablo.api.DownloadError as e:
                    logger.error(e)

    logger.info("Retrieved {} episodes".format(count))


def get_new_recordings(args):
    recordings = tablo.api.initialize_recordings()

    tablo.library.load_library(recordings)

    tablo.library.update_library(recordings)

    updated = False
    have_meta = (1 for k in recordings.values() if k.get('meta'))
    downloaded = (1 for k in recordings.values() if k.get('downloaded', False) == True)
    logger.info("{}/{} have metadata".format(sum(have_meta), len(recordings)))
    logger.info("{}/{} recordings downloaded".format(sum(downloaded), len(recordings)))

    logger.info("Downloading recording details...")
    for recording in recordings.values():
        if 'meta' not in recording or (recording['status'] != 'finished' and recording['status'] != 'failed' and recording['status'] != 'not_found'):
            try:
                tablo.api.update_recording_metadata(recording)
                recording['duplicate'] = tablo.api.is_recording_duplicate(recording, recordings)
                updated = True
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    logger.info("Recording no longer exists on server")
                    logger.debug(recording)
                    recording['status'] = 'not_found'
                    updated = True
                else:
                    raise e

    tablo.library.update_library(recordings) if updated else None

    logger.info("Building library structure...")
    for recording in recordings.values():
        if 'meta' in recording and recording['status'] == 'finished':
                tablo.api.update_recording_path(recording)
                updated = True

    tablo.library.update_library(recordings) if updated else None

    recording_repository = args.repo
    if recording_repository is None:
        recording_repository = default_recording_repository

    tablo.api.find_downloaded_recordings(recordings, recording_repository)
    tablo.library.update_library(recordings)

    shows = ['Modern Family', 'Big Bang Theory', 'NOVA', 'Nature', 'Alf', 'A-Team', 'Bill Nye the Science Guy', 'Star Trek', 'Good Place', 'Victoria', 'New Girl']

    download_and_convert_episodes(recordings, recording_repository, shows)

    tablo.library.update_library(recordings)
    logger.info("Done")

def list_library(args):
    recordings = tablo.api.initialize_recordings()
    tablo.library.load_library(recordings)

    for recording in recordings.values():
        tablo.api.update_recording_metadata(recording)
        recording['duplicate'] = tablo.api.is_recording_duplicate(recording, recordings)
        if 'episode' in recording['meta']:
            print("{}: {} -- season {} episode {} -- {} -- {}".format(
                recording['meta']['airing_details']['show_title'],
                recording['meta']['episode']['title'],
                recording['meta']['episode']['season_number'],
                recording['meta']['episode']['number'],
                recording['meta']['episode']['orig_air_date'],
                recording['status']
                ))
        else:
            print(recording['meta']['airing_details']['show_title'])

    if args.full:
        pp.pprint(recordings)
        return

def record(args):
    print(args)

if __name__ == "__main__":
    # create the top-level parser
    parser = argparse.ArgumentParser(prog='tablo')
    parser.add_argument('--version', action='store_true')
    subparsers = parser.add_subparsers(help='sub-command help')

    #parser_version = subparsers.add_parser('--version', help='Display version info')

    parser_library = subparsers.add_parser('library', help='library help')
    library_subparsers = parser_library.add_subparsers(help='sub-command help')

    library_list_parser = library_subparsers.add_parser('list', help='list library')
    library_list_parser.add_argument('--full', action='store_true', help='list all information')
    library_list_parser.set_defaults(func=list_library)

    parser_record = subparsers.add_parser('record', help='record help')
    record_subparsers = parser_record.add_subparsers(help='record sub help')

    record_new_parser = record_subparsers.add_parser('new', help='record new')
    record_new_parser.add_argument('--repo', type=str, default=default_recording_repository, help='path where converted recordings are stored')
    record_new_parser.set_defaults(func=get_new_recordings)

    # parse some argument lists
    args = parser.parse_args()
    if args.version == True:
        print("0.0.1")

    args.func(args)
