"""
Move files based on hashs

export PYTHONPATH=./
python3 apps/hash_mover.py -s ./lib/ | python3 apps/hash_mover.py -d ./lib/ --dry_run

python3 apps/hash_mover.py -s ~/temp/sync_test1/ | python3 apps/hash_mover.py -d ~/temp/sync_test2/

-on local
rm ~/Applications/KaraKara/karakara_files.remote.cache
python3 apps/hash_mover.py -s ~/Applications/KaraKara/files --cache_filename_source ~/Applications/KaraKara/karakara_files.remote.cache
scp apps/hash_mover.py violet:~/hash_mover.py
scp ~/Applications/KaraKara/karakara_files.remote.cache violet:~/karakara_files.remote.cache

-on server
python3 apps/hash_mover.py -s /data/media_upload/ --cache_filename ~/karakara_files.local.cache
python3 hash_mover.py --cache_filename_source karakara_files.remote.cache --cache_filename_destination karakara_files.local.cache --destination_folder /data/media_upload/


KARAKARA_DEBUG=True python processmedia.py process ~/Applications/KaraKara/files/


WARNING:
  possible dataloss
  rename 1.txt to temp.txt
  rename 2.txt to 1.txt
  rename temp.txt to 2.txt

  syncing this will LOOSE DATA
  There is not currently detection of files with the same name
  1.txt could be moved over 2.txt and - 2.txt is now completely the contentents of 1.txt - the contents of 2.txt is now lost

"""
import sys
import os
import hashlib
import json
import shutil
from functools import partial
from collections import defaultdict

# Some kind of fix for piping
import signal
signal.signal(signal.SIGPIPE, signal.SIG_DFL)


import logging
log = logging.getLogger(__name__)


VERSION = "0.0"
DEFAULT_IGNORE_REGEX = r'\.bak|\.git|\.DS_Store|\.txt'  # TODO: This should enforce end of string terms only
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
def file_scan(path, file_regex=None, ignore_regex=r'\.git', hasher=None, stats=False):  #, func_progress=lambda f: None
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
    for root, dirs, files in os.walk(path):
        if ignore_regex.search(root):
            continue
        for f in files:
            if file_regex.match(f) and not ignore_regex.search(f):
                yield FileScan(
                    folder=root,
                    file=f,
                    absolute=os.path.join(root, f),
                    relative=os.path.join(root.replace(path, ''), f).strip('/'),
                    hash=hashfile(os.path.join(root, f), hasher),
                    stats=stater(os.path.join(root, f)),
                )


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


#to_delete = open('/Users/allan.callaghan/Applications/KaraKara/to_delete.txt', 'a')
def func_remove(filename):
    if input('remove {0}:'.format(filename)):
        log.warn('removing {0}'.format(filename))
        #os.remove(filename)
        #to_delete.write(filename+'\n')
        #to_delete.flush()
def remove_duplicates(folder, file_regex=None, ignore_regex=None, func_remove=func_remove):
    hash_defaultdict = defaultdict(list)
    for f in file_scan(folder, file_regex=file_regex, ignore_regex=ignore_regex, hasher=hashlib.sha256):
        sys.stderr.write('.')
        sys.stderr.flush()
        files = hash_defaultdict[f.hash]
        files.append(f.relative)
        if len(files) > 1:
            log.warn('duplicates {0}'.format(files))
            func_remove(os.path.join(folder, sorted(files, key=lambda x: len(x))[0]))


folder_data = '/Users/allan.callaghan/Applications/KaraKara/files/'

def copy_missing_source(folder='/Users/allan.callaghan/temp/'):
    ff = []
    for f in file_scan(folder):
        ff.append(f.absolute)
    for root, dirs, files in os.walk(folder_data):
    #for f in file_scan('/Users/allan.callaghan/Applications/KaraKara/files/'):
        if '/source' in root and not files:
            match = re.search(r'Import - (.*)/source', root)
            if match:
                name = match.group(1)
                for f in ff:
                    if name in f:
                        print(name, f)
                        try:
                            shutil.copy2(f, root)
                        except:
                            import pdb ; pdb.set_trace()
            #import pdb ; pdb.set_trace()

#copy_missing_source()

#TEMP
def find_misplaced_source():
    for root, dirs, files in os.walk(folder_data):
        if 'source' in dirs:
            for f in files:
                if re.search(r'\.(mp4|srt|ssa|avi|mkv)$', f):
                    print(root, f)
                    shutil.move(os.path.join(root, f), '/Users/allan.callaghan/Applications/KaraKara/backup/')

#TEMP
def convert_symlinks_to_files():
    for root, dirs, files in os.walk(folder_data):
        for f in files:
            absolute_path = os.path.join(root, f)
            if (os.path.islink(absolute_path)):
                absolute_path_real = os.path.realpath(absolute_path)
                print(absolute_path)
                #print(absolute_path_real)
                #import pdb ; pdb.set_trace()
                try:
                    shutil.move(absolute_path, absolute_path+'.bak')
                    shutil.copy2(absolute_path_real, absolute_path)
                    os.remove(absolute_path+'.bak')
                except Exception as e:
                    print(e)
                    import pdb ; pdb.set_trace()




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

    # modes
    parser.add_argument('-x', '--delete_duplicates', action='store_true', help='')

    # Cache
    parser.add_argument('--cache_filename_source', action='store', help='', default=None)
    parser.add_argument('--cache_filename_destination', action='store', help='', default=None)

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

    if args.get('delete_duplicates'):
        remove_duplicates(args.get('source_folder'), file_regex=args['file_regex'], ignore_regex=args['ignore_regex'])
        exit()

    if args.get('source_folder') or args['cache_filename_source']:
        hash_files_dict = hash_files_cache(args['source_folder'], args['cache_filename_source'], func_hasher)

    if args.get('destination_folder'):
        if not hash_files_dict:
            hash_files_dict = json.load(sys.stdin)
        func_move = (lambda source, destination: log.info('Move {0} to {1}'.format(source, destination))) if args['dry_run'] else shutil.move
        move_files(hash_files_dict, args['destination_folder'], args['cache_filename_destination'], func_hasher, func_move)
    else:
        json.dump(hash_files_dict, sys.stdout)
        sys.stdout.flush()


if __name__ == "__main__":
    main()
