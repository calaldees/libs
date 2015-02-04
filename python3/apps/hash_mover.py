"""
Move files based on hashs
"""

import hashlib

from lib.misc import file_scan

import logging
log = logging.getLogger(__name__)


VERSION = "0.0"
DEFAULT_CACHE_FILENAME = 'hash.cache'

# Encode --------

import pickle
data_load = pickle.load
data_dump = pickle.dump

# ------------------------------------------------------------------------------

def hash_files(folder, file_regex=None, hasher=hashlib.sha256):
    return {
        f.hash: f
        for f in file_scan(folder, file_regex=file_regex, hasher=hasher)
    }



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
    parser.add_argument('-s', '--source_folder', action='store', help='', required=True)

    # Cache
    parser.add_argument('--cache_filename', action='store', help='', default=DEFAULT_CACHE_FILENAME)

    # Common
    parser.add_argument('--dry_run', action='store_true', help='', default=False)
    parser.add_argument('-v', '--verbose', action='store_true', help='', default=False)
    parser.add_argument('--version', action='version', version=VERSION)

    args = vars(parser.parse_args())

    return args


def main():
    args = get_args()
    logging.basicConfig(level=logging.DEBUG if args['verbose'] else logging.INFO)

    try:
        with open(args['cache_filename'], 'rb') as f:
            data = data_load(f)
    except IOError:
        with open(args['cache_filename'], 'wb') as f:
            data = hash_files(args['source_folder'])
            data_dump(data, f)

    print(data)

if __name__ == "__main__":
    main()
