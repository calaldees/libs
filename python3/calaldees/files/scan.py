import re
import os
import collections
from functools import partial
from itertools import chain
import hashlib

from .exts import file_ext


import logging
log = logging.getLogger(__name__)



def fast_scan_regex_filter(file_regex=None, ignore_regex=r'\.git'):
    if not file_regex:
        file_regex = '.*'
    if isinstance(file_regex, str):
        file_regex = re.compile(file_regex)
    if isinstance(ignore_regex, str):
        ignore_regex = re.compile(ignore_regex)
    return lambda f: file_regex.search(f.name) and not ignore_regex.search(f.name)


FileScan = collections.namedtuple('FileScan', ['folder', 'file', 'absolute', 'abspath', 'relative', 'hash', 'stats', 'ext', 'file_no_ext'])
def fast_scan(root, path=None, search_filter=fast_scan_regex_filter()):
    path = path or ''
    for dir_entry in os.scandir(os.path.join(root, path)):
        if (dir_entry.is_file() or dir_entry.is_symlink()) and search_filter(dir_entry):  # .is_symlink is dangerious, as symlinks can also be folders
            file_no_ext, ext = file_ext(dir_entry.name)
            yield FileScan(
                folder=path,
                file=dir_entry.name,
                absolute=dir_entry.path,  # This is wrong. This is NOT absolute! We need to unpick this. Call this variable 'path' or something and have absolute actually be the absolute.
                abspath=os.path.abspath(dir_entry.path),
                relative=dir_entry.path.replace(root, '').strip('/'),
                stats=dir_entry.stat(),
                ext=ext,
                file_no_ext=file_no_ext,
                hash=LazyString(partial(hashfile, dir_entry.path)),
            )
        if dir_entry.is_dir():
            for sub_dir_entry in fast_scan(root, os.path.join(path, dir_entry.name), search_filter):
                yield sub_dir_entry



def hashfile(filehandle, hasher=hashlib.sha256, blocksize=65535):
    if not hasher:
        return
    if isinstance(filehandle, str):
        filename = filehandle
        if not os.path.isfile(filename):
            log.warn('file to hash does not exist {}'.format(filename))
            return ''
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
