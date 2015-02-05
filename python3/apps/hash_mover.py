"""
Move files based on hashs

export PYTHONPATH=./
python3 apps/hash_mover.py -s ./lib/ | python3 apps/hash_mover.py -d ./lib/ --dry_run

"""
import sys
import hashlib
import json
import select
import signal
from functools import partial
import shutil
import os

signal.signal(signal.SIGPIPE, signal.SIG_DFL)

from lib.misc import file_scan

import logging
log = logging.getLogger(__name__)


VERSION = "0.0"
DEFAULT_IGNORE_REGEX = r'\.bak|\.git'
DEFAULT_FILE_REGEX = r'.*'

# Encode --------

import pickle
data_load = pickle.load
data_dump = pickle.dump


# Utils ------------------------------------------------------------------------

def has_pipe_input():
    return select.select([sys.stdin, ], [], [], 0.0)[0]


# ------------------------------------------------------------------------------

def hash_files(folder, file_regex=None, ignore_regex=None, hasher=hashlib.sha256, func_progress=lambda f: None):
    return {
        f.hash: f.relative
        for f in file_scan(folder, file_regex=file_regex, ignore_regex=ignore_regex, hasher=hasher, func_progress=func_progress)
    }


def hash_files_cache(folder, cache_filename, func_hasher):
    assert folder
    file_dict = {}
    if cache_filename:
        try:
            with open(cache_filename, 'rb') as f:
                file_dict = data_load(f)
            log.info('Loaded data from cache - {0}'.format(cache_filename))
        except IOError:
            pass

    if not file_dict:
        file_dict = func_hasher(folder)

        if cache_filename:
            with open(cache_filename, 'wb') as f:
                data_dump(file_dict, f)
            log.info('Saving cache data - {0}'.format(cache_filename))

    return file_dict


def move_files(file_dict_remote, destination_folder, cache_filename, func_hasher, func_move=shutil.move):
    assert file_dict_remote
    assert destination_folder
    assert func_hasher

    file_dict_local = func_hasher(destination_folder, cache_filename)

    for key in file_dict_remote.keys() & file_dict_local.keys():
        func_move(
            os.path.join(destination_folder, file_dict_local[key]),
            os.path.join(destination_folder, file_dict_remote[key]),
        )


# Command Line -----------------------------------------------------------------

def get_args():
    import argparse
    parser = argparse.ArgumentParser(
        description="""
        Dropbox style move on hashs
        """,
        epilog=""" """
    )

    # Folders
    parser.add_argument('-s', '--source_folder', action='store', help='')
    parser.add_argument('-d', '--destination_folder', action='store', help='')

    # Cache
    parser.add_argument('--cache_filename', action='store', help='', default=None)

    # Selection
    parser.add_argument('--file_regex', action='store', help='', default=DEFAULT_FILE_REGEX)
    parser.add_argument('--ignore_regex', action='store', help='', default=DEFAULT_IGNORE_REGEX)

    # Common
    parser.add_argument('--dry_run', action='store_true', help='', default=False)
    parser.add_argument('-v', '--verbose', action='store_true', help='', default=False)
    parser.add_argument('--version', action='version', version=VERSION)

    args = vars(parser.parse_args())

    return args


def main():
    args = get_args()
    logging.basicConfig(level=logging.DEBUG if args['verbose'] else logging.INFO)

    func_hasher = partial(hash_files, file_regex=args['file_regex'], ignore_regex=args['ignore_regex'])
    hash_files_dict = None

    if args.get('source_folder'):
        hash_files_dict = hash_files_cache(args['source_folder'], args['cache_filename'], func_hasher)

    if args.get('destination_folder'):
        if not hash_files_dict:
            hash_files_dict = json.load(sys.stdin)
        func_move = lambda source, destination: log.info('Move {0} to {1}'.format(source, destination)) if args['dry_run'] else shutil.move
        move_files(hash_files_dict, args['destination_folder'], args['cache_filename'], func_hasher, func_move)
    else:
        json.dump(hash_files_dict, sys.stdout)
        sys.stdout.flush()


if __name__ == "__main__":
    main()
