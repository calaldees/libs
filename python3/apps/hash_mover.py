"""
Move files based on hashs

export PYTHONPATH=./
python3 apps/hash_mover.py -s ./lib/ | python3 apps/hash_mover.py -d ./lib/ --dry_run

python3 apps/hash_mover.py -s ~/temp/sync_test1/ | python3 apps/hash_mover.py -d ~/temp/sync_test2/

"""
import sys
import os
import hashlib
import json
import shutil
from functools import partial


# Some kind of fix for piping
import signal
signal.signal(signal.SIGPIPE, signal.SIG_DFL)


import logging
log = logging.getLogger(__name__)


VERSION = "0.0"
DEFAULT_IGNORE_REGEX = r'\.bak|\.git'
DEFAULT_FILE_REGEX = r'.*'

# Encode --------

#import pickle
data_load = json.load  # pickle.load
data_dump = json.dump  # pickle.dump


# Misc Utils -------------------------------------------------------------------
#
# file_scan is copy and patsted from misc.py so this script can be used as a standalone
# if these methods are changed they should also be reflected upstream

#from lib.misc import file_scan
import collections
import re

FileScan = collections.namedtuple('FileScan', ['folder', 'file', 'absolute', 'relative', 'hash', 'stats'])
def file_scan(path, file_regex=None, ignore_regex=r'\.git', hasher=None, stats=False, func_progress=lambda f: None):
    """
    return (folder, file, folder+file, folder-path+file)
    """
    stater = (lambda f: os.stat(f)) if stats else (lambda f: None)
    if not file_regex:
        file_regex = '.*'
    if isinstance(file_regex, str):
        file_regex = re.compile(file_regex)
    if isinstance(ignore_regex, str):
        ignore_regex = re.compile(ignore_regex)

    log.debug('Scanning files in {0}'.format(path))
    file_list = []
    for root, dirs, files in os.walk(path):
        if ignore_regex.search(root):
            continue
        for f in files:
            if file_regex.match(f) and not ignore_regex.search(f):
                file_details = FileScan(
                    folder=root,
                    file=f,
                    absolute=os.path.join(root, f),
                    relative=os.path.join(root.replace(path, ''), f).strip('/'),
                    hash=hashfile(os.path.join(root, f), hasher),
                    stats=stater(os.path.join(root, f)),
                )
                file_list.append(file_details)
                func_progress(file_list)

    return file_list


def hashfile(filehandle, hasher=hashlib.sha256, blocksize=65536):
    if not hasher:
        return
    if isinstance(filehandle, str):
        filename = filehandle
        filehandle = open(filename, 'rb')
    hasher = hasher()
    buf = filehandle.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = filehandle.read(blocksize)
    digest = hasher.hexdigest()
    if filename:
        filehandle.close()
        log.debug('hashfile - {0} - {1}'.format(digest, filename))
    return digest


# ------------------------------------------------------------------------------

class ProgressCounter(object):

    def __init__(self, DOTS_PER_FILE=1, out=sys.stderr):
        self.DOTS_PER_FILE = DOTS_PER_FILE
        self.file_count = 0
        self.out = out

    def progress(self, file_list):
        ticks = len(file_list) - self.file_count
        if ticks > self.DOTS_PER_FILE:
            self.out.write('.')
            self.out.flush()
            self.file_count += ticks

progress_counter = ProgressCounter()


def hash_files(folder, file_regex=None, ignore_regex=None, hasher=hashlib.sha256, func_progress=progress_counter.progress):
    return {
        f.hash: f.relative
        for f in file_scan(folder, file_regex=file_regex, ignore_regex=ignore_regex, hasher=hasher, func_progress=func_progress)
    }


def hash_files_cache(folder, cache_filename, func_hasher):
    assert folder
    file_dict = {}
    if cache_filename:
        try:
            with open(cache_filename, 'r') as f:
                file_dict = data_load(f)
            log.info('Loaded data from cache - {0}'.format(cache_filename))
        except IOError:
            pass
        except Exception:
            log.warn('cache file is corrupted - removing {0}'.format(cache_filename))
            os.remove(cache_filename)

    if not file_dict:
        file_dict = func_hasher(folder)

        if cache_filename:
            with open(cache_filename, 'w') as f:
                data_dump(file_dict, f)
            log.info('Saving cache data - {0}'.format(cache_filename))

    return file_dict


def move_files(file_dict_remote, destination_folder, cache_filename, func_hasher, func_move=shutil.move):
    assert file_dict_remote
    assert destination_folder
    assert func_hasher

    file_dict_local = hash_files_cache(destination_folder, cache_filename, func_hasher)

    for key in file_dict_remote.keys() & file_dict_local.keys():
        if file_dict_local[key] != file_dict_remote[key]:
            source_file = os.path.join(destination_folder, file_dict_local[key])
            destination_file = os.path.join(destination_folder, file_dict_remote[key])

            # Create destination folders if needed
            destination_path = os.path.dirname(destination_file)
            if not os.path.exists(destination_path):
                os.makedirs(destination_path)

            func_move(source_file, destination_file)


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

    if args['dry_run']:
        log.warn('dry_run is not implemented properly, it still creates folders')

    if args.get('source_folder'):
        hash_files_dict = hash_files_cache(args['source_folder'], args['cache_filename'], func_hasher)

    if args.get('destination_folder'):
        if not hash_files_dict:
            hash_files_dict = json.load(sys.stdin)
        func_move = (lambda source, destination: log.info('Move {0} to {1}'.format(source, destination))) if args['dry_run'] else shutil.move
        move_files(hash_files_dict, args['destination_folder'], args['cache_filename'], func_hasher, func_move)
    else:
        json.dump(hash_files_dict, sys.stdout)
        sys.stdout.flush()


if __name__ == "__main__":
    main()
