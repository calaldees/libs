import threading
import time
import multiprocessing
import collections
from itertools import chain

from .scan import fast_scan

DEFAULT_RESCAN_INTERVAL = 2.0

def file_scan_diff_thread(paths, onchange_function=None, rescan_interval=DEFAULT_RESCAN_INTERVAL, **kwargs):
    """
    Used in a separate thread to indicate if a file has changed
    Use onchange_function if working in a single thread mode
    """
    rescan_interval = rescan_interval or DEFAULT_RESCAN_INTERVAL
    assert rescan_interval > 0

    if isinstance(paths, str):
        paths = paths.split(',')

    FileScanDiffItem = collections.namedtuple('FileScanDiffItem', ('abspath', 'relative', 'mtime'))  # 'folder', 'file', 'abspath', 'ext', 'file_no_ext'
    #FILE_SCAN_FIELDS = set(FileScanDiffItem._fields) & set(FileScan._fields)
    def scan_set(paths):
        return {
            FileScanDiffItem(
                abspath=f.abspath,
                relative=f.relative,
                mtime=f.stats.st_mtime,
                #**{k: v for k, v in f._asdict().items() if k in FILE_SCAN_FIELDS}
            )
            for f in chain(*(fast_scan(path, **kwargs) for path in paths))
        }

    queue = multiprocessing.Queue()
    report_filechange = onchange_function if onchange_function else queue.put
    def scan_loop():
        reference_scan = scan_set(paths)
        while True:
            this_scan = scan_set(paths)
            changed_files_diff = reference_scan ^ this_scan
            if changed_files_diff:
                reference_scan = this_scan
                report_filechange({(f.relative, f.abspath) for f in changed_files_diff})
            time.sleep(rescan_interval)

    if onchange_function:
        scan_loop()
    else:
        thread = threading.Thread(target=scan_loop, args=())  # May need to update this with python3 way of threading
        thread.daemon = True
        thread.start()

        return queue
