from .scan import fast_scan
from ..data import defaultdict_recursive


class FolderStructure(object):

    @staticmethod
    def factory(path, **kwargs):
        files = defaultdict_recursive()

        def set_leaf(f):
            files_item = files
            for path_segment in filter(None, f.folder.split('/')):
                files_item = files_item[path_segment]
            files_item[f.file] = f
        for f in fast_scan(path, **kwargs):
            set_leaf(f)

        return FolderStructure(files, None)

    def __init__(self, files_item, parent=None, name=None):
        self._files_item = dict(files_item)
        self._parent = parent
        self._name = name
        for key, value in self._files_item.items():
            if isinstance(value, dict):
                self._files_item[key] = FolderStructure(value, parent=self, name=key)

    def __str__(self):
        return 'parent={parent} name={name}\n{folders}\n{files}'.format(
            parent=self.parent.name if self.parent else '',
            name=self.name,
            folders='\n'.join('/{0}'.format(f.name) for f in self.folders),
            files='\n'.join('{0}'.format(f.file) for f in self.files),
        )

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
        if path and isinstance(path, str):
            path = list(path.split('/'))
        if path:
            try:
                item = self._files_item[path.pop(0)]
            except KeyError:
                return None
            if isinstance(item, FolderStructure):
                return item.get(path)
            else:
                return item
        else:
            return self

    def scan(self, select_function):
        """
        recusivly look trhough files and yeild files in turn
        """
        for file_item in self._files_item.values():
            if isinstance(file_item, FolderStructure):
                for f in file_item.scan(select_function):
                    yield f
            elif select_function(file_item):
                yield file_item

    @property
    def all_files(self):
        return self.scan(lambda f: True)
