from unittest.mock import mock_open


class MultiMockOpen(object):
    def __init__(self, *args, **kwargs):
        self.handlers = {}

    def add_handler(self, filename, read_data):
        self.handlers[filename] = read_data

    def open(self, full_path, *args, **kwargs):
        for filename, reads in self.handlers.items():
            if filename in full_path:
                return mock_open(read_data=self.handlers[filename])
        assert full_path in self.handlers, 'Unknown file to mock {0}'.format(full_path)

