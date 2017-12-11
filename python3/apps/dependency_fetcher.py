import os
import json
import hashlib
import operator
import urllib.request
from functools import partial
from collections import namedtuple

import logging
log = logging.getLogger(__name__)


VERSION = '0.0.0'
DEFAULT_TRACKER_FILENAME = 'dependency_fetcher.data.json'


def hash_datastructure(data):
    hash = hashlib.sha1()
    hash.update(str(data).encode())
    return hash.hexdigest()


SourceDestinationFilename = namedtuple('SourceDestinationFilename', ('source', 'destination'))
def split_destination_filename(filename):
    filenames = tuple(map(lambda s: s.strip(), filename.split(' -> ')))
    if len(filenames) == 1:
        filenames = filenames * 2
    return SourceDestinationFilename(*filenames)


def _fetch_file(fetch_function, source, destination, overwrite=False):
    log.debug('{source} -> {destination}'.format(source=source, destination=destination))  # TODO: replace with formatstring
    if not overwrite and os.path.exists(destination):
        log.debug('{destination} already exists'.format(destination=destination))  # TODO: replace with formatstring
        return True
    try:
        os.makedirs(os.path.dirname(destination))
    except:
        pass
    try:
        fetch_function(source, destination)
        return True
    except Exception:
        log.info('Unable to fetch {source} -> {destination} with {fetch_function}'.format(source=source, destination=destination, fetch_function=fetch_function))  # TODO: replace with formatstring
        return False
FetchFileMethod = namedtuple('FetchFileMethod', ('source_check', 'fetch_method'))
FETCH_FILE_METHODS = [
    FetchFileMethod(lambda text: '://' in text, partial(_fetch_file, urllib.request.urlretrieve)),
]
def fetch_file(source, destination):
    for source_check, fetch_method in FETCH_FILE_METHODS:
        if source_check(source):
            return fetch_method(source, destination)
    return False


def fetch(data, destination_path, clean=False):
    destination_path = os.path.join(destination_path, data.get('destination', ''))
    # Normalize sources list
    if isinstance(data['sources'], str):
        data['sources'] = (data['sources'], )
    # Attempt sources in order
    for source_path in data['sources']:
        log.debug('Attempting source_path {source_path}'.format(source_path))  # TODO: replace with formatstring
        def replace_data_placeholders(text):
            return text.replace('VERSION', data['VERSION'])
        source_path = replace_data_placeholders(source_path)
        def _fetch_file(filename):
            _split_destination_filename = split_destination_filename(replace_data_placeholders(filename))
            source_filename = os.path.join(source_path, _split_destination_filename.source)
            destination_filename = os.path.join(destination_path, _split_destination_filename.destination)
            if clean and os.path.exists(destination_filename):
                os.remove(destination_filename)
            return fetch_file(source_filename, destination_filename)
        # All fetched files should return True. `all` with short circit and abort on any false and attempt next source
        fetched = all(map(_fetch_file, data['files']))
        if fetched:
            return True
    return False


def main():
    args = get_args()
    logging.basicConfig(level=args['loglevel'])

    with open(args['dependencies_datafile'], 'rt') as filehandle:
        dependencies_data = json.load(filehandle)

    # All source paths are based off the 'path' of the dependencies_datafile
    base_path = os.path.abspath(os.path.dirname(args['dependencies_datafile']))

    # Dynamically add the file fetcher method now the base path is known
    FETCH_FILE_METHODS.append(
        FetchFileMethod(
            os.path.exists,
            lambda source, *args, **kwargs: _fetch_file(
                os.link,
                os.path.normpath(os.path.join(base_path, source)),
                *args, **kwargs
            )
        )
    )

    # Open previously downloaded/links tracker state
    if os.path.exists(args['tracker']):
        with open(args['tracker'], 'rt') as filehandle:
            tracker = json.load(filehandle)
    else:
        tracker = {}
    tracker_state_start = set(tracker.values())

    # Iterate over dependencies
    for name, data in dependencies_data.items():
        log.debug('{name}'.format(name=name))  # TODO: replace with formatstring
        hashcode = hash_datastructure(data)
        # If not downloaded/linked before
        if tracker.get(name) != hashcode or args.get('force'):
            # Fetch the files
            log.info(f"""Fetching {name} {data.get('VERSION')}""")
            if fetch(data, args['destination_path'], clean=True):
                tracker[name] = hashcode

    # Store current downloaded/linked state of the downloaded files
    tracker_state_end = set(tracker.values())
    if tracker_state_start != tracker_state_end:
        with open(args['tracker'], 'wt') as filehandle:
            json.dump(tracker, filehandle)


def get_args():
    import argparse

    parser = argparse.ArgumentParser(
        description="""Download dependencies
        From symlinks locally or external urls
        """,
        epilog=""""""
    )
    parser.add_argument('dependencies_datafile', nargs='?', help='the json data file of the dependencies', default='dependency_fetcher.json')
    parser.add_argument('--destination_path', help='destination to place dependencies', default='./')
    parser.add_argument('--tracker', help='persistent tracker file for installed versions', default=DEFAULT_TRACKER_FILENAME)
    parser.add_argument('--loglevel', type=int, default=logging.INFO)
    parser.add_argument('--version', action='version', version=VERSION)

    args = vars(parser.parse_args())

    if os.path.isdir(args['tracker']):
        args['tracker'] = os.path.join(args['tracker'], DEFAULT_TRACKER_FILENAME)

    return args


def postmortem(func, *args, **kwargs):
    import traceback
    import pdb
    import sys
    try:
        func(*args, **kwargs)
    except Exception:
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        pdb.post_mortem(tb)


if __name__ == "__main__":
    postmortem(main)
