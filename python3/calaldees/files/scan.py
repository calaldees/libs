import re
import os
import collections
from functools import partial
from itertools import chain
import hashlib

from .exts import file_ext
from ..lazy import LazyString



import logging
log = logging.getLogger(__name__)


DEFAULT_IGNORE_REGEX = r'^\.|/\.|^__|/__'  # Ignore folders starting with '.' or '__' by default

def fast_scan_regex_filter(file_regex=None, ignore_regex=DEFAULT_IGNORE_REGEX):
    if not file_regex:
        file_regex = '.*'
    if isinstance(file_regex, str):
        file_regex = re.compile(file_regex)
    if isinstance(ignore_regex, str):
        ignore_regex = re.compile(ignore_regex)
    return lambda f: file_regex.search(f) and not ignore_regex.search(f)


FileScan = collections.namedtuple('FileScan', ['folder', 'file', 'absolute', 'abspath', 'relative', 'hash', 'stats', 'ext', 'file_no_ext'])
def fast_scan(root, path=None, search_filter=fast_scan_regex_filter()):
    path = path or ''
    for dir_entry in os.scandir(os.path.join(root, path)):
        _relative = dir_entry.path.replace(root, '').strip('/')
        if (dir_entry.is_file() or dir_entry.is_symlink()) and search_filter(_relative):  # .is_symlink is dangerious, as symlinks can also be folders
            file_no_ext, ext = file_ext(dir_entry.name)
            yield FileScan(
                folder=path,
                file=dir_entry.name,
                absolute=dir_entry.path,  # This is wrong. This is NOT absolute! We need to unpick this. Call this variable 'path' or something and have absolute actually be the absolute.
                abspath=os.path.abspath(dir_entry.path),
                relative=_relative,
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


def hash_data(data, hasher=hashlib.sha256):
    hasher = hasher()
    hasher.update(str(data).encode())
    return hasher.hexdigest()


def hashfiles(*args, **kwargs):
    """
    use same args as fast_scan
    """
    file_hashs = tuple(sorted(
        (filescan.relative, filescan.hash)
        for filescan in fast_scan(*args, **kwargs)
    ))
    return hash_data(file_hashs)
