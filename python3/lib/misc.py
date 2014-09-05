import re
import random
import datetime
import dateutil.parser
import os
import json
import zlib
import hashlib
import collections
import shutil
import itertools

dateutil_parser = dateutil.parser.parser()

try:
    from pyramid.settings import asbool
except ImportError:
    # Fallback without pyramid - This fallback needs consideration
    asbool = bool

import logging
log = logging.getLogger(__name__)


# TODO - @property to get/set now?
_now_override = None
def now(new_override=None):
    global _now_override
    if new_override:
        _now_override = new_override
    if _now_override:
        return _now_override
    return datetime.datetime.now()

import inspect
def funcname(level=1):
    """Use: print("My name is: %s" % inspect.stack()[0][3])"""
    return inspect.stack()[level][3]


# Reference - http://stackoverflow.com/questions/2182858/how-can-i-pack-serveral-decorators-into-one
def decorator_combine(*dec_funs):
    def _inner_chain(f):
        for dec in reversed(dec_funs):
            f = dec(f)
        return f
    return _inner_chain


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
    def loads(json_string):
        if isinstance(json_string, bytes):
            json_string = json_string.decode('utf-8')
        return json_load(json_string)
    def dumps(obj):
        return json_string(obj).encode('utf-8')


def read_json(filename):
    with open(filename, 'r') as source:
        #try:
        if hasattr(source,'read'):
            data = source.read()
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        return json.loads(data)
        #except Exception as e:
        #    log.warn('Failed to process %s' % source)


FileScan = collections.namedtuple('FileScan', ['folder', 'file', 'absolute', 'relative'])
def file_scan(path, file_regex, ignore_regex=r'\.git'):
    """
    return (folder, file, folder+file, folder-path+file)
    """
    if isinstance(file_regex, str):
        file_regex = re.compile(file_regex)
    if isinstance(ignore_regex, str):
        ignore_regex = re.compile(ignore_regex)

    log.debug('Scanning files in {0}'.format(path))
    file_list = []
    for root, dirs, files in os.walk(path):
        if ignore_regex.search(root):
            continue
        file_list += [FileScan(root, f, os.path.join(root, f), os.path.join(root.replace(path, ''), f).strip('/'))
                      for f in files if file_regex.match(f)]
    return file_list


def hash_data(data):
    hash = hashlib.sha1()
    hash.update(str(data).encode())
    return hash.hexdigest()


def hash_files(files):
    """
    adler32 is a good-enough checksum that's fast to compute.
    """
    return "%X" % abs(hash(frozenset(zlib.adler32(open(_file,'rb').read()) for _file in files)))


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

    ## Can't rely on dict order between versions of python - fix this test 
    ##>>> a = {'a': 1, 'b': 2}
    ##>>> update_dict(a, {'b': 3, 'c': 3})
    ##{'a': 1, 'c': 3, 'b': 3}
    """
    dict_a.update(dict_b)
    return dict_a


def random_string(length=8):
    """
    Generate a random string of a-z A-Z 0-9
    (Without vowels to stop bad words from being generated!)

    >>> len(random_string())
    8
    >>> len(random_string(10))
    10

    If random, it should compress pretty badly:

    # TODO (python3 needs a buffer here)
    #>>> import zlib
    #>>> len(zlib.compress(random_string(100))) > 50
    True
    """
    random_symbols = '1234567890bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ'
    r = ''
    for i in range(length):
        r += random_symbols[random.randint(0,len(random_symbols)-1)]
    return r


def substring_in(substrings, string_list, ignore_case=True):
    """
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
    if   len(time_components) == 1:
        seconds = time_components[0]
    elif len(time_components) == 2:
        hours = time_components[0]
        minutes = time_components[1]
    elif len(time_components) == 3:
        hours   = time_components[0]
        minutes = time_components[1]
        seconds = time_components[2]
    second_components = seconds.split('.')
    if len(second_components) == 2:
        seconds      = second_components[0]
        milliseconds = second_components[1]
    hours = int(hours)
    minutes = int(minutes)
    seconds = int(seconds)
    milliseconds = int(milliseconds)
    assert hours>=0
    assert minutes>=0
    assert seconds>=0
    assert milliseconds==0, 'milliseconds are not implemented properly .01 is parsed as int(01), this is incorrect, fix this!' 
    return datetime.timedelta(
        seconds      = seconds + minutes*60 + hours*60*60,
        milliseconds = milliseconds
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
        if isinstance(d,t):
            return [strip_non_base_types(value) for value in d]
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
    """
    if not isinstance(value_string, str):
        return value_string
    try:
        value, return_type = value_string.split(value_split)
        return convert_str(value.strip(), return_type.strip())
    except (ValueError, AttributeError) as e:
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

    def __missing__ (self, key):
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
