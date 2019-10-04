import os.path
import json
import urllib.request
import urllib.parse
from datetime import datetime
from collections import defaultdict
from contextlib import contextmanager
from functools import lru_cache, partial


class HTTPFolder():
    """
    Wrapper to browse/walk remote files served via http
    Designed to work with nginx json index format
    See test_http_folder.pt for examples
    """

    class RemoteFile():
        def __init__(self, item, with_filehandle):
            assert isinstance(item, dict)
            assert item['type'] == 'file'
            self.name = item['name']
            self.size = item['size']
            self.with_filehandle = with_filehandle
            self._mtime = item['mtime']
        @property
        def mtime(self):
            return datetime.strptime(self._mtime, '%a, %d %b %Y %H:%M:%S %Z')

    def __init__(self, url):
        assert '?' not in url, 'TODO: handle query string'
        self.url = self._normalize_directory(url)

    @staticmethod
    def _normalize_directory(path):
        if not path.endswith('/'):
            path = f'{path}/'
        return path

    @staticmethod
    @lru_cache()
    def _get_json(url):
        with urllib.request.urlopen(url) as f:
            return json.load(f)

    def walk(self, relative_path='./', url=None):
        """
        Rough equivalent of os.walk - https://docs.python.org/3/library/os.html#os.walk
        """
        url = url or self.url
        items = defaultdict(list)
        for item in self._get_json(url):
            items[item['type']].append(item['name'])
        yield (relative_path, items['directory'], items['file'])
        for directory in items['directory']:
            yield from self.walk(
                relative_path=os.path.join(relative_path, directory),
                url=self._normalize_directory(os.path.join(url, urllib.parse.quote(directory))),
            )

    @contextmanager
    def open(self, path):
        with urllib.request.urlopen(os.path.join(self.url, os.path.normpath(urllib.parse.quote(path)))) as f:
            yield f

    @property
    def files(self):
        return (
            self.RemoteFile(item=item, with_filehandle=partial(self.open, item['name']))
            for item in self._get_json(self.url)
            if item['type'] == 'file'
        )

    @property
    def directorys(self):
        return (
            HTTPFolder(os.path.join(self.url, urllib.parse.quote(item['name'])))
            for item in self._get_json(self.url)
            if item['type'] == 'directory'
        )
