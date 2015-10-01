import os.path

from .misc import file_scan, defaultdict_recursive


class FolderStructure(object):

    @staticmethod
    def factory(path, **kwargs):
        files = defaultdict_recursive()

        def set_leaf(f):
            files_item = files
            for path_segment in os.path.split(f.folder):
                files_item = files_item[path_segment]
            files_item[f.file] = f
        for f in file_scan(path, stats=True, **kwargs):
            set_leaf(f)

        def insert_parent_reference(files_item, parent=None):
            if not isinstance(files_item, dict):
                return
            files_item['..'] = parent
            for file_item_child in files_item.values():
                insert_parent_reference(file_item_child, files_item)
        insert_parent_reference(files)

    def __init__(self, files_item):
        self.files_item = files_item if files_item else {}

    def get_folders(self):
        for key, value in self.files_item.items():
            if isinstance(value, FolderStructure):
                yield value

    def get_files(self):
        for key, value in self.files_item.items():
            if not isinstance(value, FolderStructure):
                yield value

    def get_parent(self):
        return FolderStructure(self.files_item.get('..'))

    def scan(self, file_regex=None, ignore_regex=None):
        """
        recusivly look trhough files and yeild files in turn
        """
        for file_item in self.files_item.values():
            if (isinstance(file_item, FolderStructure)):
                for f in file_item.scan(file_regex, ignore_regex):
                    yield f
            elif file_regex.search(file_item.file) and not ignore_regex.search(file_item.file):
                yield f
