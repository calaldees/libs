import json
import datetime
import enum
import re

from .date_tools import dateutil_parser


class JSONObjectEncoder(json.JSONEncoder):
    def default(self, obj):
        """
        Used with json lib to serialize json output
        e.g
        text = json.dumps(result, cls=JSONObjectEncoder)
        """
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        if isinstance(obj, datetime.timedelta):
            return obj.total_seconds()
        if isinstance(obj, set):
            return tuple(obj)
        if isinstance(obj, enum.Enum):
            return '__enum__.{type}.{name}.{value}'.format(type=type(obj).__name__, name=obj.name, value=obj.value)
        # Let the base class default method raise the TypeError
        return super().default(obj)

_json_object_handler = JSONObjectEncoder().default
def json_object_handler(obj):
    """
    >>> json_object_handler(datetime.datetime(year=2000, month=1, day=1))
    '2000-01-01T00:00:00'
    >>> json_object_handler(datetime.timedelta(days=1, seconds=1))
    86401.0
    >>> TestEnum = enum.Enum('TestEnum', ('a', 'b'))
    >>> json_object_handler(TestEnum.b)
    '__enum__.TestEnum.b.2'
    >>> sorted(json_object_handler({'a','b','c'}))
    ['a', 'b', 'c']
    >>> json_object_handler({'a': 23})
    {'a': 23}
    >>> json_object_handler(23)
    23
    """
    try:
        return _json_object_handler(obj)
    except TypeError:
        return obj


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
            return dateutil_parser.parse(obj)
        if re.match(r'__enum__\.(?P<type>.+)\.(?P<name>.+)\.(?P<value>\d+)', obj):
            # TODO: Require register dispatch methods for registering enum types
            # This should be split into another module
            raise NotImplementedError('Enum decoding requires implementing')
    return obj


def json_string(data):
    """
    >>> import datetime
    >>> json_string({'a': {'b': datetime.datetime(day=1, month=1, year=1980), 'c': {1,2,3}, 'd': 23}})
    '{"a": {"b": "1980-01-01T00:00:00", "c": [1, 2, 3], "d": 23}}'
    """
    return json.dumps(data, cls=JSONObjectEncoder)


def json_load(json_string):
    return json_object_handler_inverse(json.loads(json_string))


class JSONSerializer():
    """
    http://docs.pylonsproject.org/projects/pyramid/en/master/api/session.html#pyramid.session.SignedCookieSessionFactory
    An object with two methods:
        loads and dumps.
    The loads method should accept bytes and return a Python object.
    The dumps method should accept a Python object and return bytes.
    A ValueError should be raised for malformed inputs.
    """
    @staticmethod
    def loads(data):
        return json_load(data.decode('utf-8') if isinstance(data, bytes) else data)

    @staticmethod
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
        #    log.warning('Failed to process %s' % source)
