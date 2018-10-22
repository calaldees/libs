import re
import collections


FileExt = collections.namedtuple('FileExt', ('filename', 'ext'))
def file_ext(filename):
    """
    >>> file_ext('test.txt')
    FileExt(filename='test', ext='txt')
    >>> file_ext('test')
    ('test', '')
    >>> file_ext('test.again.yaml')
    FileExt(filename='test.again', ext='yaml')
    >>> file_ext('.doc')
    FileExt(filename='', ext='doc')
    """
    try:
        return FileExt(*re.match('(.*)\.(.*?)$', filename).groups())
    except AttributeError:
        return (filename, '')


def file_extension_regex(exts):
    return re.compile(r'|'.join(map(lambda e: r'\.{0}$'.format(e), exts)))


def get_fileext(filename):
    try:
        return re.search(r'\.([^\.]+)$', filename).group(1).lower()
    except:
        return None
