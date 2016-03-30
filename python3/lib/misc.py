import re
import random
import datetime
import os
import json
import zlib
import hashlib
import collections
import shutil
import colorsys
import codecs
import time
import threading
from itertools import chain
from functools import partial

try:
    from pyramid.settings import asbool
except ImportError:
    # Fallback without pyramid - This fallback needs consideration
    def asbool(arg):
        if isinstance(arg, str):
            return arg.lower().strip() in ('yes', 'true', 'ok', 'y')
        return bool(arg)

try:
    import dateutil.parser
    dateutil_parser = dateutil.parser.parser()
except ImportError:
    dateutil_parser = lambda x: None


import logging
log = logging.getLogger(__name__)


def duplicates(list_with_duplicates):
    """
    todo: tests
    """
    if not isinstance(list_with_duplicates, (list, tuple)):
        list_with_duplicates = tuple(list_with_duplicates)
    set_without_duplicates = set(list_with_duplicates)
    if len(set_without_duplicates) == len(list_with_duplicates):
        return []
    return [item for item in list_with_duplicates if not set_without_duplicates.pop(item)]


def freeze(items):
    """
    todo: tests
    """
    if isinstance(items, dict):
        items = items.items()
    if not isinstance(items, str) and hasattr(items, '__iter__'):
        return frozenset(freeze(item) for item in items)
    return items

def postmortem(func):
    import traceback
    import pdb
    import sys
    try:
        func()
    except Exception:
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        pdb.post_mortem(tb)


def null_function(*args, **kwargs):
    pass


def first(iterable):
    """
    Return the first non null value in an iterable

    TODO: tests
    """
    if not iterable:
        return None
    for i in iterable:
        if i:
            return i


def flatten(l):
    """
    http://stackoverflow.com/questions/2158395/flatten-an-irregular-list-of-lists-in-python

    >>> list(flatten([[[1, 2, 3], [4, 5]], 6]))
    [1, 2, 3, 4, 5, 6]
    """
    for el in l:
        if isinstance(el, collections.Iterable) and not isinstance(el, (str, bytes)):
            for sub in flatten(el):
                yield sub
        else:
            yield el

def get_item_or_attr(obj, item_or_attr_name):
    if hasattr(obj, item_or_attr_name):
        return getattr(obj, item_or_attr_name)
    if hasattr(obj, 'get'):
        return obj.get(item_or_attr_name)
    return None


def get_obj(cmd, obj, cmd_separator='.'):
    """
    Iterate though a chain of objects trying to find a function specifyed with a dot separated name

    TODO: doctests
    """
    if isinstance(cmd, str):
        cmd = cmd.split(cmd_separator)
    if isinstance(obj, (list, tuple)):
        return get_obj(cmd, {getattr(o, '__name__', None) or type(o).__name__: o for o in obj})
    if len(cmd) == 1:
        return get_item_or_attr(obj, cmd.pop(0))
    if len(cmd) > 1:
        next_cmd = cmd.pop(0)
        next_obj = get_item_or_attr(obj, next_cmd)
        # TODO:  Maybe? If next_obj is noarg function, then run it to get the return value?
        return get_obj(cmd, next_obj)
    return None


def run_funcs(data, obj, fallback=null_function):
    """
    Trigger data are decompacted from json
    This json could be a list or a single dict
    If the data is a list then run each item
    If a single item, run the item

    The data items dict should contain a function name to run in '.' separated format

    TODO: doctests
    """
    if isinstance(data, (list, tuple)):
        for item in data:
            run_funcs(item, obj, fallback)
    elif isinstance(data, dict):
        func = get_obj(data.get('func', ''), obj)
        getattr(func, '__call__', fallback)(data)


def subdict(d, keys):
    return {k: v for k, v in d.items() if k in keys}


def list_neighbor_generator(_list, out_of_bounds_type=dict):
    """
    Todo - this is rubish - replace with zip()

    >>> ['{0}:{1}:{2}'.format(prev, current, next) for prev, current, next in list_neighbor_generator([1,2,3], out_of_bounds_type=str)]
    [':1:2', '1:2:3', '2:3:']
    """
    length = len(_list)
    for index, item in enumerate(_list):
        yield _list[index-1] if index > 0 else out_of_bounds_type(), item, _list[index+1] if index < length-1 else out_of_bounds_type()


# TODO - @property to get/set now?
_now_override = None
def now(new_override=None):
    global _now_override
    if new_override:
        _now_override = new_override
    if _now_override:
        return _now_override
    return datetime.datetime.now()


def epoc(datetime_obj):
    return (datetime_obj - datetime.datetime.utcfromtimestamp(0)).total_seconds()


import inspect
def funcname(level=1):
    """
    Use: print("My name is: %s" % inspect.stack()[0][3])
    >>> def test():
    ...     return funcname()
    >>> test()
    'test'
    """
    return inspect.stack()[level][3]


def postmortem(func, *args, **kwargs):
    import traceback
    import pdb
    import sys
    try:
        return func(*args, **kwargs)
    except:
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        pdb.post_mortem(tb)


# Reference - http://stackoverflow.com/questions/2182858/how-can-i-pack-serveral-decorators-into-one
def decorator_combine(*dec_funs):
    def _inner_chain(f):
        for dec in reversed(dec_funs):
            f = dec(f)
        return f
    return _inner_chain


def cmd_args(*args, **kwargs):
    """
    >>> cmd_args('cmd', '-flag')
    ('cmd', '-flag')
    >>> cmd_args('cmd', 'arg1', flag=None, value='1', value2=2, value3=False)
    ('cmd', 'arg1', '-flag', '-value', '1', '-value2', '2', '-value3', 'False')
    """
    def format_arg(k, v):
        arg = []
        if k:
            arg.append('-{0}'.format(k))
        if v != None:
            arg.append(str(v))
        return arg
    return tuple(args) + tuple(x for k in sorted(kwargs.keys()) for x in format_arg(k, kwargs[k]))


def json_object_handler(obj):
    """
    Used with json lib to serialize json output
    e.g
    text = json.dumps(result, default=json_object_handler)

    >>> json_object_handler(datetime.datetime(year=2000, month=1, day=1))
    '2000-01-01T00:00:00'
    >>> json_object_handler(datetime.timedelta(days=1, seconds=1))
    86401.0
    >>> sorted(json_object_handler({'a','b','c'}))
    ['a', 'b', 'c']
    """
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    if isinstance(obj, datetime.timedelta):
        return obj.total_seconds()
    if isinstance(obj, set):
        return tuple(obj)
    raise TypeError


def json_object_handler_inverse(obj):
    """
    Totally inefficent re-date json parser thing ... blarg ...
    TODO: Tests
    """
    if isinstance(obj, dict):
        return {k: json_object_handler_inverse(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [json_object_handler_inverse(o) for o in obj]
    if isinstance(obj, str):
        if re.match(r'\d+-\d+-\d+T\d+:\d+:\d+', obj):
            return convert_str(obj, datetime.datetime)
    return obj


def json_string(data):
    return json.dumps(data, default=json_object_handler)


def json_load(json_string):
    return json_object_handler_inverse(json.loads(json_string))


class json_serializer(object):
    """
    http://docs.pylonsproject.org/projects/pyramid/en/master/api/session.html#pyramid.session.SignedCookieSessionFactory
    An object with two methods:
        loads and dumps.
    The loads method should accept bytes and return a Python object.
    The dumps method should accept a Python object and return bytes.
    A ValueError should be raised for malformed inputs.
    """
    def loads(data):
        return json_load(data.decode('utf-8') if isinstance(data, bytes) else data)
    def dumps(obj):
        return json_string(obj).encode('utf-8')


def read_json(filename):
    with open(filename, 'r') as source:
        #try:
        if hasattr(source, 'read'):
            data = source.read()
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        return json.loads(data)
        #except Exception as e:
        #    log.warn('Failed to process %s' % source)


def read_file_list(filename):
    data = []
    with open(filename, 'r') as source:
        for line in source:
            data.append(line.strip())
    return data


FileExt = collections.namedtuple('FileExt', ('filename', 'ext'))
def file_ext(filename):
    """
    >>> file_ext('test.txt')
    FileExt(filename='test', ext='txt')
    >>> file_ext('test')
    ('test', '')
    >>> file_ext('test.again.yaml')
    FileExt(filename='test.again', ext='yaml')
    >>> file_ext('.doc')
    FileExt(filename='', ext='doc')
    """
    try:
        return FileExt(*re.match('(.*)\.(.*?)$', filename).groups())
    except AttributeError:
        return (filename, '')

def file_extension_regex(exts):
    return re.compile(r'|'.join(map(lambda e: r'\.{0}$'.format(e), exts)))

FileScan = collections.namedtuple('FileScan', ['folder', 'file', 'absolute', 'relative', 'hash', 'stats', 'ext', 'file_no_ext'])
def file_scan(path, file_regex=None, ignore_regex=r'\.git', hasher=None, stats=False):
    """
    regex's are for filenames only (not the whole path). That feature could be added

    return (folder, file, folder+file, folder-path+file)
    """
    stater = (lambda f: os.stat(f)) if stats else (lambda f: None)
    if not file_regex:
        file_regex = '.*'
    if isinstance(file_regex, str):
        file_regex = re.compile(file_regex)
    if isinstance(ignore_regex, str):
        ignore_regex = re.compile(ignore_regex)

    log.debug('Scanning files in {0}'.format(path))
    for root, dirs, files in os.walk(path):
        if ignore_regex.search(root):
            continue
        for f in files:
            if file_regex.search(f) and not ignore_regex.search(f):
                file_no_ext, ext = file_ext(f)
                yield FileScan(
                    folder=root,
                    file=f,
                    absolute=os.path.join(root, f),
                    relative=os.path.join(root.replace(path, ''), f).strip('/'),
                    hash=hashfile(os.path.join(root, f), hasher),
                    stats=stater(os.path.join(root, f)),
                    ext=ext,
                    file_no_ext=file_no_ext,
                )


def fast_scan_regex_filter(file_regex=None, ignore_regex=r'\.git'):
    if not file_regex:
        file_regex = '.*'
    if isinstance(file_regex, str):
        file_regex = re.compile(file_regex)
    if isinstance(ignore_regex, str):
        ignore_regex = re.compile(ignore_regex)
    return lambda f: file_regex.search(f.name) and not ignore_regex.search(f.name)


def fast_scan(root, path=None, search_filter=fast_scan_regex_filter()):
    path = path or ''
    for dir_entry in os.scandir(os.path.join(root, path)):
        if dir_entry.is_file() and search_filter(dir_entry):
            file_no_ext, ext = file_ext(dir_entry.name)
            yield FileScan(
                folder=path,
                file=dir_entry.name,
                absolute=dir_entry.path,
                relative=dir_entry.path.replace(root, '').strip('/'),
                stats=dir_entry.stat(),
                ext=ext,
                file_no_ext=file_no_ext,
                hash=LazyString(partial(hashfile, dir_entry.path)),
            )
        if dir_entry.is_dir():
            for sub_dir_entry in fast_scan(root, os.path.join(path, dir_entry.name), search_filter):
                yield sub_dir_entry



def file_scan_diff_thread(paths, onchange_function, rescan_interval=2.0, **kwargs):
    """
    Used in a separate thread to indicate if a file has changed
    """
    if not rescan_interval:
        log.info('No scan interval, file_scan_diff_thread not started')
        return
    if isinstance(paths, str):
        paths = paths.split(',')
    kwargs['stats'] = True
    def scan_set():
        return {'|'.join((f.relative, str(f.stats.st_mtime))) for f in chain(*(file_scan(path, **kwargs) for path in (paths)))}

    def scan_loop():
        reference_scan = scan_set()
        while True:
            this_scan = scan_set()
            changed_files = reference_scan ^ this_scan
            if changed_files:
                reference_scan = this_scan
                onchange_function(changed_files)
            time.sleep(rescan_interval)

    thread = threading.Thread(target=scan_loop, args=())
    thread.daemon = True
    thread.start()


def hashfile(filehandle, hasher=hashlib.sha256, blocksize=65536):
    if not hasher:
        return
    if isinstance(filehandle, str):
        filename = filehandle
        filehandle = open(filename, 'rb')
    hasher = hasher()
    buf = filehandle.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = filehandle.read(blocksize)
    digest = hasher.hexdigest()
    if filename:
        filehandle.close()
        log.debug('hashfile - {0} - {1}'.format(digest, filename))
    return digest


class LazyString(object):
    def __init__(self, generate_function):
        self.generate_function = generate_function
        self.generated_value = None

    def __str__(self):
        if not self.generated_value:
            self.generated_value = self.generate_function()
        return self.generated_value

    def __unicode__(self):
        return self.__str__()

    def __repr__(self):
        return self.__str__()


def hash_files(files, hasher=zlib.adler32):
    """
    adler32 is a good-enough checksum that's fast to compute.
    """
    return "%X" % abs(hash(frozenset(hasher(open(_file, 'rb').read()) for _file in files)))


def hash_data(data, hasher=hashlib.sha256):
    hasher = hasher()
    hasher.update(str(data).encode())
    return hasher.hexdigest()


def get_fileext(filename):
    try:
        return re.search(r'\.([^\.]+)$', filename).group(1).lower()
    except:
        return None


def extract_subkeys(data, subkey):
    """
    >>> sorted(extract_subkeys({'a.a':1, 'a.b':2, 'b.a': 3}, 'a.').items())
    [('a', 1), ('b', 2)]
    """
    return {k.replace(subkey, ''): v for k, v in data.items() if k.startswith(subkey)}


def update_dict(dict_a, dict_b):
    """
    Because dict.update(d) does not return the new dict

    Updates dict_a with the contents of dict_b

    >>> a = {'a': 1, 'b': 2}
    >>> sorted(update_dict(a, {'b': 3, 'c': 3}).items())
    [('a', 1), ('b', 3), ('c', 3)]
    """
    dict_a.update(dict_b)
    return dict_a


def random_string(length=8):
    """
    TODO: Depricated! Moved to string_tools
    
    Generate a random string of a-z A-Z 0-9
    (Without vowels to stop bad words from being generated!)

    >>> len(random_string())
    8
    >>> len(random_string(10))
    10

    If random, it should compress pretty badly:

    >>> import zlib
    >>> len(zlib.compress(random_string(100).encode('utf-8'))) > 50
    True
    """
    random_symbols = '1234567890bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ'
    r = ''
    for i in range(length):
        r += random_symbols[random.randint(0, len(random_symbols)-1)]
    return r


def substring_in(substrings, string_list, ignore_case=True):
    """
    TODO - Depricated! Moved to string_tools
    
    Find a substrings in a list of string_list
    Think of it as
      is 'bc' in ['abc', 'def']

    >>> substring_in( 'bc'      , ['abc','def','ghi'])
    True
    >>> substring_in( 'jkl'     , ['abc','def','ghi'])
    False
    >>> substring_in(['zx','hi'], ['abc','def','ghi'])
    True
    >>> substring_in(['zx','yw'], ['abc','def','ghi'])
    False
    """
    if not string_list or not substrings:
        return False
    if isinstance(substrings, str):
        substrings = [substrings]
    if not hasattr(string_list, '__iter__') or not hasattr(substrings, '__iter__'):
        raise TypeError('params mustbe iterable')
    for s in string_list:
        if not s:
            continue
        if ignore_case:
            s = s.lower()
        for ss in substrings:
            if ignore_case:
                ss = ss.lower()
            if ss in s:
                return True
    return False


def normalize_datetime(d=None, accuracy='hour'):
    """
    Normalizez datetime down to hour or day
    Dates are immutable (thank god)
    """
    if not d:
        d = now()
    if not accuracy or accuracy == 'none':
        return None
    elif accuracy == 'hour':
        return d.replace(minute=0, second=0, microsecond=0)
    elif accuracy == 'day' :
        return d.replace(minute=0, second=0, microsecond=0, hour=0)
    elif accuracy == 'week':
        return d.replace(minute=0, second=0, microsecond=0, hour=0) - datetime.timedelta(days=d.weekday())
    return d


def parse_timedelta(text):
    """
    Takes string and converts to timedelta

    ##>>> parse_timedelta('00:01:00.01')
    ##datetime.timedelta(0, 60, 1)

    >>> parse_timedelta('00:00:01.00')
    datetime.timedelta(0, 1)
    >>> parse_timedelta('01:00:00')
    datetime.timedelta(0, 3600)
    >>> parse_timedelta('5')
    datetime.timedelta(0, 5)
    >>> parse_timedelta('1:01')
    datetime.timedelta(0, 3660)
    """
    hours = "0"
    minutes = "0"
    seconds = "0"
    milliseconds = "0"
    time_components = text.strip().split(':')
    if len(time_components) == 1:
        seconds = time_components[0]
    elif len(time_components) == 2:
        hours = time_components[0]
        minutes = time_components[1]
    elif len(time_components) == 3:
        hours = time_components[0]
        minutes = time_components[1]
        seconds = time_components[2]
    second_components = seconds.split('.')
    if len(second_components) == 2:
        seconds = second_components[0]
        milliseconds = second_components[1]
    hours = int(hours)
    minutes = int(minutes)
    seconds = int(seconds)
    milliseconds = int(milliseconds)
    assert hours >= 0
    assert minutes >= 0
    assert seconds >= 0
    assert milliseconds == 0, 'milliseconds are not implemented properly .01 is parsed as int(01), this is incorrect, fix this!' 
    return datetime.timedelta(
        seconds=seconds + minutes*60 + hours*60*60,
        milliseconds=milliseconds
    )


def strip_non_base_types(d):
    """
    Recursively steps though a python dictionary
    Identifies strings and removes/replaces harmful/unwanted characters + collapses white space

    (The tests below rely on the dict ordering in the output, if pythons dict ordering changes this will break)

    >>> strip_non_base_types('a')
    'a'

    ## Cant reply on dict order between versions of python
    ##>>> strip_non_base_types({'a':1, 'b':'2', 'c':[3,4,5], 'd':{'e':'6'}})
    ##{'a': 1, 'c': [3, 4, 5], 'b': '2', 'd': {'e': '6'}}
    ##>>> strip_non_base_types({'a':1, 'b':'2', 'c':[3,4,5], 'd':{'e':datetime.datetime.now()}})
    ##{'a': 1, 'c': [3, 4, 5], 'b': '2', 'd': {'e': None}}

    """
    for t in [str, int, float, bool]:
        if isinstance(d, t):
            return d
    if hasattr(d, 'items'):
        return {key: strip_non_base_types(value) for key, value in d.items()}
    for t in [list, set, tuple]:
        if isinstance(d, t):
            return [strip_non_base_types(v) for v in d]
    return None


def convert_str_with_type(value_string, value_split='->', fallback_type=None):
    """
    >>> convert_str_with_type("5 -> int")
    5
    >>> convert_str_with_type("00:00:01 -> timedelta")
    datetime.timedelta(0, 1)
    >>> convert_str_with_type("2000-01-01 -> datetime")
    datetime.datetime(2000, 1, 1, 0, 0)
    >>> convert_str_with_type("[]")
    []
    >>> convert_str_with_type('', fallback_type=list)
    []
    """
    if not isinstance(value_string, str):
        return value_string
    try:
        value, return_type = value_string.split(value_split)
        return convert_str(value.strip(), return_type.strip() or fallback_type)
    except (ValueError, AttributeError):
        return convert_str(value_string.strip(), fallback_type)


def convert_str(value, return_type):
    """
    >>> convert_str('', 'None')

    >>> convert_str('bob', None)
    'bob'
    >>> convert_str('1', int)
    1
    >>> convert_str('yes', 'bool')
    True
    >>> convert_str('[]', None)
    []
    >>> convert_str('[bob]', None)
    ['bob']
    >>> convert_str('[a  ,b,c]', None)
    ['a', 'b', 'c']
    >>> convert_str('a,b ,c', 'list')
    ['a', 'b', 'c']
    >>> convert_str('[a,b,c]', 'list')
    ['a', 'b', 'c']
    >>> convert_str('', list)
    []
    >>> convert_str('[true, yes, no, false]', 'bool')
    [True, True, False, False]
    >>> convert_str('{"a":1}', None)
    {'a': 1}
    >>> convert_str('2000-01-01', 'datetime')
    datetime.datetime(2000, 1, 1, 0, 0)
    >>> convert_str('0:00:01', 'timedelta')
    datetime.timedelta(0, 1)
    """
    if return_type == 'None':
        return None
    if not value and (return_type == 'list' or return_type == list):
        return []
    if not value or not isinstance(value, str) or return_type == str or return_type == 'str':
        return value
    if value.startswith('[') and value.endswith(']'):
        value = value[1:-1]
        if not value:
            return []
        if return_type == 'list' or return_type == list:  # If already a list, revert to string contents
            return_type = str
        return [convert_str(v.strip(), return_type) for v in value.split(',')]
    if value.startswith('{') and value.endswith('}'):
        return json_load(value)
    if not return_type:
        return value
    if return_type == 'bool' or return_type == bool:
        return asbool(value)
    if return_type == 'int' or return_type == int:
        return int(value)
    if return_type == 'float' or return_type == float:
        return float(value)
    if return_type == 'time' or return_type == datetime.time:
        return dateutil_parser.parse(value).time()
    if return_type == 'date' or return_type == datetime.date:
        return dateutil_parser.parse(value).date()
    if return_type == 'datetime' or return_type == datetime.datetime:
        return dateutil_parser.parse(value)
    if return_type == 'timedelta' or return_type == datetime.timedelta:
        return parse_timedelta(value)
    if return_type == 'list' or return_type == list:
        return [v.strip() for v in value.split(',') if v.strip()]
    if return_type == 'jsonfile':
        return read_json(value)
    if return_type == 'listfile':
        return read_file_list(value)
    assert False, 'unable to convert {0} to {1}'.format(value, return_type)


#http://stackoverflow.com/questions/4126348/how-do-i-rewrite-this-function-to-implement-ordereddict/4127426#4127426
class OrderedDefaultdict(collections.OrderedDict):
    def __init__(self, *args, **kwargs):
        if not args:
            self.default_factory = None
        else:
            if not (args[0] is None or callable(args[0])):
                raise TypeError('first argument must be callable or None')
            self.default_factory = args[0]
            args = args[1:]
        super(OrderedDefaultdict, self).__init__(*args, **kwargs)

    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        self[key] = default = self.default_factory()
        return default

    def __reduce__(self):  # optional, for pickle support
        args = self.default_factory if self.default_factory else tuple()
        return type(self), args, None, None, self.items()

    def last(self):
        return reversed(self).__next__()


def defaultdict_recursive():
    return collections.defaultdict(defaultdict_recursive)


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


def limit(value, min_value=0.0, max_value=1.0):
    """
    >>> limit(0, 0, 1)
    0
    >>> limit(0.5, 0, 1)
    0.5
    >>> limit(100, 0, 1)
    1
    >>> limit(-100.11, 0.0, 1.1)
    0.0
    >>> limit(-57, -50, 50)
    -50
    >>> limit(57, -50, 50)
    50
    """
    return max(min_value, min(max_value, value))


def parse_rgb_color(color, fallback_color=(0.0, 0.0, 0.0, 0.0)):
    """
    Normalise a range of string values into (r,g,b) tuple from 0 to 1

    >>> parse_rgb_color('what is this?')
    (0.0, 0.0, 0.0, 0.0)
    >>> parse_rgb_color((1,1,1))
    (1.0, 1.0, 1.0)
    >>> parse_rgb_color([0,0.5,1])
    (0.0, 0.5, 1.0)
    >>> parse_rgb_color('#FFFFFF')
    (1.0, 1.0, 1.0)
    >>> parse_rgb_color('#FFFFFFFF')
    (1.0, 1.0, 1.0, 1.0)
    >>> parse_rgb_color('hsv:0,1,1')
    (1.0, 0.0, 0.0)
    >>> parse_rgb_color('hls:0,1,1')
    (1.0, 1.0, 1.0)
    >>> parse_rgb_color('yiq:0,0,0')
    (0.0, 0.0, 0.0)
    >>> parse_rgb_color('hsv:0,1,1,0.5')
    (1.0, 0.0, 0.0, 0.5)
    >>> parse_rgb_color('rgb:1,1,1')
    (1.0, 1.0, 1.0)
    >>> parse_rgb_color('rgb:1,1,1,1')
    (1.0, 1.0, 1.0, 1.0)
    >>> parse_rgb_color(0.5)
    (0.5, 0.5, 0.5, 0.5)
    """
    if isinstance(color, float):
        color = (color, ) * 4
    if isinstance(color, (tuple, list)):
        return tuple(map(float, color))
    if isinstance(color, str):
        if color.startswith('#'):
            return tuple(map(lambda v: limit(v/255, 0.0, 1.0), codecs.decode(color.strip('#'), "hex")))
        elif color.find(':') >= 0:
            color_type, value = color.split(':')
            values = tuple(map(float, value.split(',')))
            if color_type == 'rgb':
                return values
            return getattr(colorsys, '{0}_to_rgb'.format(color_type))(*values[0:3]) + values[3:]
    if fallback_color:
        return fallback_color
    raise AttributeError('{0} is not parseable'.format(color))


def one_to_limit(value, limit=255):
    """
    >>> one_to_limit(0, limit=255)
    0
    >>> one_to_limit(1, limit=255)
    255
    >>> one_to_limit(0.5, limit=255)
    127
    """
    return min(int(value * limit), limit)


def byte_limit(value):
    """
    >>> byte_limit(255)
    255
    >>> byte_limit(256)
    255
    >>> byte_limit(0)
    0
    >>> byte_limit(-1)
    0
    """
    return limit(value, min_value=0, max_value=255)


def one_byte_limit(value):
    return byte_limit(one_to_limit(value, limit=255))


def color_distance(target, actual, threshold=20):
    """
    >>> color_distance((0,0,0), (0,0,0))
    0
    >>> color_distance((0,0,255), (1,18,255))
    19
    >>> color_distance((255,0,0), (0,0,255))
    >>> color_distance((0,0,0), (10,10,10))
    """
    distance = sum(abs(a - b) for a, b in zip(target, actual))
    return distance if distance < threshold else None


def color_close(target, actual, threshold=20):
    distance = color_distance(target, actual, threshold)
    return True if distance is not None else False
