import os.path

from .misc import fast_scan, defaultdict_recursive


class FolderStructure(object):

    @staticmethod
    def factory(path, **kwargs):
        files = defaultdict_recursive()

        def set_leaf(f):
            files_item = files
            for path_segment in f.folder.split('/'):  # os.path.split(f.folder):
                files_item = files_item[path_segment]
            files_item[f.file] = f
        for f in fast_scan(path, **kwargs):  # stats=True,
            set_leaf(f)

        return FolderStructure(files, None)

    def __init__(self, files_item, parent=None, name=None):
        self._files_item = files_item
        self._parent = parent
        self._name = name
        for key, value in self._files_item.items():
            if isinstance(value, dict):
                files_item[key] = FolderStructure(value, parent=self, name=key)

    @property
    def folders(self):
        for value in self._files_item.values():
            if isinstance(value, FolderStructure):
                yield value

    @property
    def files(self):
        for value in self._files_item.values():
            if not isinstance(value, FolderStructure):
                yield value

    @property
    def parent(self):
        return self._parent

    @property
    def name(self):
        return self._name

    def get(self, path):
        if isinstance(path, str):
            path = list(path.split('/'))  # os.path.split(path)
        if path:
            item = self._files_item[path.pop(0)]
            if isinstance(item, FolderStructure):
                return item.get(path)
            else:
                return item
        else:
            return self

    def scan(self, file_regex=None, ignore_regex=None):
        """
        recusivly look trhough files and yeild files in turn
        """
        for file_item in self._files_item.values():
            if isinstance(file_item, FolderStructure):
                for f in file_item.scan(file_regex, ignore_regex):
                    yield f
            elif (file_regex and file_regex.search(file_item.file)) and (not ignore_regex or not ignore_regex.search(file_item.file)):
                yield file_item
