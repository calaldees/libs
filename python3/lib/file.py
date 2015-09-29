import os.path

from .misc import file_scan, defaultdict_recursive


class FolderStructure(object):

    @staticmethod
    def factory(path):
        files = defaultdict_recursive()

        def set_leaf(f):
            files_item = files
            for path_segment in os.path.split(f.folder):
                files_item = files_item[path_segment]
            files_item[f.file] = f
        for f in file_scan(path, stats=True):
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
        return ()

    def get_files(self):
        return ()

    def get_parent(self):
        return FolderStructure(self.files_item.get('..'))