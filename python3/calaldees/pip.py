
import re
import io
REGEX_COMMENT = re.compile(r'#(.*)')
def load_pip_requires_file(filename, _open=io.open):
    """
    >>> def _mock_open(data):
    ...     class _mock_open_class():
    ...         def __init__(self, *args, **kwargs):
    ...             pass
    ...         def __enter__(self):
    ...             return data
    ...         def __exit__(self, type, value, traceback):
    ...             pass
    ...     return _mock_open_class
    >>> load_pip_requires_file('test.txt', _mock_open('''
    ...     # unneeded==3.4.5  # comment
    ...     # other==1.2.3
    ...     testlib>=5.6.7
    ...     
    ...     myApp # is great
    ... '''.splitlines()))
    ('testlib>=5.6.7', 'myApp')
    """
    with _open(filename, 'rt') as filehandle:
        return tuple(filter(None, (
            REGEX_COMMENT.sub('', line).strip()
            for line in filehandle
        )))
