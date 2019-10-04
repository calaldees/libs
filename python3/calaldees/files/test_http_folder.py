import os
from contextlib import contextmanager
from datetime import datetime

from .http_folder import HTTPFolder


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


def test_HTTPFolder():
    patcher = patch('urllib.request.urlopen', mock_server)
    patcher.start()

    rf = HTTPFolder('http://localhost/')
    remote_root_directorys = tuple(rf.directorys)
    assert len(remote_root_directorys) == 1
    remote_root_directory = remote_root_directorys[0]
    assert remote_root_directory.url == 'http://localhost/test%20me/'
    remote_test_files = tuple(remote_root_directorys[0].files)
    assert len(remote_test_files) == 1
    remote_data_file = remote_test_files[0]
    assert remote_data_file.name == 'data.json'
    assert remote_data_file.mtime == datetime(2019, 10, 4, 6, 48, 3)
    with remote_data_file.with_filehandle() as filehandle:
        assert filehandle.read() == """[{"key": "value"}]"""

    patcher.stop()


def test_HTTPFolder_walk():
    patcher = patch('urllib.request.urlopen', mock_server)
    patcher.start()

    rf = HTTPFolder('http://localhost/')
    rf_walk = tuple(rf.walk())
    assert rf_walk == (
        ('.', ['test me'], ['folders_and_known_fileexts.conf']),
        ('./test me', [], ['data.json']),
    )
    with rf.open(os.path.join('./test me', 'data.json')) as filehandle:
        assert filehandle.read() == """[{"key": "value"}]"""

    patcher.stop()

def test_HTTPFolder_listdir():
    patcher = patch('urllib.request.urlopen', mock_server)
    patcher.start()

    rf = HTTPFolder('http://localhost/')
    assert tuple(rf.listdir()) == ('test me', 'folders_and_known_fileexts.conf')
    assert tuple(rf.listdir('.')) == ('test me', 'folders_and_known_fileexts.conf')
    assert tuple(rf.listdir('./')) == ('test me', 'folders_and_known_fileexts.conf')
    assert tuple(rf.listdir('./test me')) == ('data.json', )
    assert tuple(rf.listdir('./test me/')) == ('data.json', )

    patcher.stop()


def test_HTTPFolder_isfile():
    patcher = patch('urllib.request.urlopen', mock_server)
    patcher.start()

    rf = HTTPFolder('http://localhost/')
    assert rf.isdir('test me')
    assert rf.isdir('./test me')
    assert rf.isdir('./test me/')
    assert not rf.isdir('folders_and_known_fileexts.conf')
    assert not rf.isfile('test me')
    assert rf.isfile('folders_and_known_fileexts.conf')

    patcher.stop()
