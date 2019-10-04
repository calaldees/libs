import os.path
import json
import urllib.request
import urllib.parse
import dateparser
from collections import defaultdict
from contextlib import contextmanager
from functools import lru_cache, partial


class RemoteFile():
    def __init__(self, item, with_filehandle):
        assert isinstance(item, dict)
        assert item['type'] == 'file'
        self.name = item['name']
        self.mtime = dateparser.parse(item['mtime'])
        self.size = item['size']
        self.with_filehandle = with_filehandle


class RemoteFolder():

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
            return json.load(f)  # #f.info()

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
            RemoteFile(item=item, with_filehandle=partial(self.open, item['name']))
            for item in self._get_json(self.url)
            if item['type'] == 'file'
        )

    @property
    def directorys(self):
        return (
            RemoteFolder(os.path.join(self.url, urllib.parse.quote(item['name'])))
            for item in self._get_json(self.url)
            if item['type'] == 'directory'
        )


from unittest.mock import patch
MOCK_SERVER = {
    'http://localhost/': """[
        {"name": "test me", "type": "directory", "mtime": "Thu, 03 Oct 2019 15:52:39 GMT"},
        {"name": "folders_and_known_fileexts.conf", "type": "file", "mtime": "Thu, 03 Oct 2019 13:08:39 GMT", "size": 597}
    ]""",
    'http://localhost/test%20me/': """[
        { "name":"data.json", "type":"file", "mtime":"Fri, 04 Oct 2019 06:48:03 GMT", "size":19 }
    ]""",
    'http://localhost/test%20me/data.json': """[{"key": "value"}]"""
}
@contextmanager
def mock_server(url):
    class mock_filehandle():
        def read(self):
            return MOCK_SERVER[url]
    yield mock_filehandle()
def test_RemoteFolder():
    patcher = patch('urllib.request.urlopen', mock_server)
    patcher.start()
    rf = RemoteFolder('http://localhost/')
    remote_root_directorys = tuple(rf.directorys)
    assert len(remote_root_directorys) == 1
    remote_root_directory = remote_root_directorys[0]
    assert remote_root_directory.url == 'http://localhost/test%20me/'
    remote_test_files = tuple(remote_root_directorys[0].files)
    assert len(remote_test_files) == 1
    remote_data_file = remote_test_files[0]
    assert remote_data_file.name == 'data.json'
    with remote_data_file.with_filehandle() as filehandle:
        assert filehandle.read() == """[{"key": "value"}]"""
    patcher.stop()
def test_RemoteFolder_walk():
    patcher = patch('urllib.request.urlopen', mock_server)
    patcher.start()
    rf = RemoteFolder('http://localhost/')
    rf_walk = tuple(rf.walk())
    assert rf_walk == (
        ('./', ['test me'], ['folders_and_known_fileexts.conf']),
        ('./test me', [], ['data.json']),
    )
    with rf.open(os.path.join('./test me', 'data.json')) as filehandle:
        assert filehandle.read() == """[{"key": "value"}]"""
    patcher.stop()
