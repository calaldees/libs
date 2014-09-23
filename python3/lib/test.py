from unittest.mock import Mock



class MultiMockOpen(object):
    def __init__(self, *args, **kwargs):
        self.handlers = {}

    def add_handler(self, filename, read_data):
        self.handlers[filename] = read_data

    def open(self, full_path, *args, **kwargs):
        for filename, reads in self.handlers.items():
            if filename in full_path:
                _open = Mock()
                _open.read.return_value = reads
                _open.__exit__ = lambda *args, **kwargs: None
                _open.__enter__ = lambda *args, **kwargs: _open
                return _open
        assert full_path in self.handlers, 'Unknown file to mock {0}'.format(full_path)

