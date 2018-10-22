import os
import re

import shutil


def backup(source_filename, destination_folder=None, func_copy=shutil.copy, func_list=os.listdir, func_exisits=os.path.exists):
    """
    >>> _func = dict( \
            func_copy    = lambda a,b: '{0} -> {1}'.format(a,b), \
            func_list    = lambda a  : ['a.txt', 'a.txt.1.bak', 'a.txt.2.bak'], \
            func_exisits = lambda a  : True, \
        )
    >>> backup('./a.txt', **_func)
    './a.txt -> ./a.txt.3.bak'
    >>> backup('./b.txt', **_func)
    './b.txt -> ./b.txt.1.bak'
    >>> backup('./c.txt', '/home/test/', **_func)
    './c.txt -> /home/test/c.txt.1.bak'
    """
    if not destination_folder:
        destination_folder = os.path.dirname(source_filename)
    if not func_exisits(destination_folder):
        os.makedirs(destination_folder)
    def get_backup_number_from_filename(filename):
        try:
            return int(re.match(r'.*\.(\d+)\.bak', filename).group(1))
        except (AttributeError, TypeError):
            return 0
    filename = os.path.basename(source_filename)
    new_backup_number = 1 + max(
            [0] + [get_backup_number_from_filename(f) for f in func_list(destination_folder) if filename in f]
    )
    backup_filename = os.path.join(destination_folder, '{0}.{1}.bak'.format(filename, new_backup_number))
    return func_copy(source_filename, backup_filename)

