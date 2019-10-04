import os.path
import json
import re
import urllib.request
import urllib.parse
from datetime import datetime
from collections import defaultdict
from contextlib import contextmanager
from functools import lru_cache, partial


class HTTPFolder():
    """
    Wrapper to simulate `os.(walk, listdir, path.isfile)` functions with remote files served via http
    Designed to work with nginx json index format
    See test_http_folder.py for examples of use

    docker run --rm -it --name nginx-autoindex-test -v $(pwd)/folders_and_known_fileexts.conf:/etc/nginx/nginx.conf:ro -v $(pwd)/:/srv/root/:ro -p 80:80 nginx:alpine
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
        self.url = self._append_path('', url=url)

    def _append_path(self, path, url=None, _enforce_folder=True):
        url = url or self.url
        path = urllib.parse.quote(os.path.normpath(path))
        path = re.sub(r'^[./]*', '', path)
        path = os.path.join(url, path)
        if _enforce_folder:
            if not path.endswith('/'):
                path = f'{path}/'
        return path

    @staticmethod
    @lru_cache()
    def _get_json(url):
        with urllib.request.urlopen(url) as f:
            return json.load(f)

    def walk(self, path='.', url=None):
        """
        https://docs.python.org/3/library/os.html#os.walk
        """
        url = url or self.url
        items = defaultdict(list)
        for item in self._get_json(url):
            items[item['type']].append(item['name'])
        yield (path, items['directory'], items['file'])
        for directory in items['directory']:
            yield from self.walk(
                path=os.path.join(path, directory),
                url=self._append_path(directory, url=url),
            )
    def listdir(self, path='.'):
        """
        https://docs.python.org/3/library/os.html#os.listdir
        Can also be context manager?
        """
        return (
            item['name']
            for item in self._get_json(self._append_path(path))
        )
    def scandir(self, *args, **kwargs):
        """
        https://docs.python.org/3/library/os.html#os.scandir
        """
        return self.listdir(*args, **kwargs)
    def isfile(self, path):
        raise NotImplementedError()
    def isdir(self, path):
        raise NotImplementedError()

    @contextmanager
    def open(self, path):
        with urllib.request.urlopen(self._append_path(path, _enforce_folder=False)) as f:
            yield f

    @property
    def files(self):
        return (
            self.__class__.RemoteFile(item=item, with_filehandle=partial(self.open, item['name']))
            for item in self._get_json(self.url)
            if item['type'] == 'file'
        )

    @property
    def directorys(self):
        return (
            self.__class__(os.path.join(self.url, urllib.parse.quote(item['name'])))
            for item in self._get_json(self.url)
            if item['type'] == 'directory'
        )
