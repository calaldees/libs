import datetime

from .json import read_json, json_load
from .date_tools import dateutil_parser, parse_timedelta


try:
    from pyramid.settings import asbool
except ImportError:
    # Fallback without pyramid - This fallback needs consideration
    def asbool(arg):
        if isinstance(arg, str):
            return arg.lower().strip() in ('yes', 'true', 'ok', 'y')
        return bool(arg)




def convert_str_with_type(value_string, value_split='->', fallback_type=None):
    """
    >>> convert_str_with_type("5 -> int")
    5
    >>> convert_str_with_type("00:00:01 -> timedelta")
    datetime.timedelta(0, 1)
    >>> convert_str_with_type("[]")
    []
    >>> convert_str_with_type('', fallback_type=list)
    []

    #>>> convert_str_with_type("2000-01-01 -> datetime")
    #datetime.datetime(2000, 1, 1, 0, 0)
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
    TODO: make this return tuples and not lists

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
    >>> convert_str('[a,,b,c,]', 'list')
    ['a', 'b', 'c']
    >>> convert_str('', list)
    []
    >>> convert_str('[true, yes, no, false]', 'bool')
    [True, True, False, False]
    >>> convert_str('{"a":1}', None)
    {'a': 1}
    >>> convert_str('0:00:01', 'timedelta')
    datetime.timedelta(0, 1)

    #>>> convert_str('2000-01-01', 'datetime')
    #datetime.datetime(2000, 1, 1, 0, 0)
    """
    _is_none = lambda x: x is not None and x != ''
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
        return list(filter(_is_none, (convert_str(v.strip(), return_type) for v in value.split(','))))
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
        return list(filter(_is_none, (v.strip() for v in value.split(','))))
    if return_type == 'jsonfile':
        return read_json(value)
    #if return_type == 'listfile':
    #    return read_file_list(value)
    assert False, 'unable to convert {0} to {1}'.format(value, return_type)


def _string_list_format_hack(value):
    """
    An inverse hack for convert_str list format
    """
    # Hack to fix reverting to empty list
    #if value == []:
    #    return '[]'
    if isinstance(value, (list, tuple)):
        return f"[{', '.join(map(str,value))}]"
    return value