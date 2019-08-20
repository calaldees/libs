
import re
import io
REGEX_COMMENT = re.compile(r'(?:[\s^]#(.*))|(git\+.*)')
def parse_requirements(filename, _open=io.open):
    """
    https://stackoverflow.com/a/16624700/3356840
    from pip.req import parse_requirements

    This is a backwards compatable python2 re-implementation

    >>> def _mock_open(data):
    ...     class _mock_open_class():
    ...         def __init__(self, *args, **kwargs):
    ...             pass
    ...         def __enter__(self):
    ...             return data
    ...         def __exit__(self, type, value, traceback):
    ...             pass
    ...     return _mock_open_class
    >>> parse_requirements('test.txt', _mock_open('''
    ...     # unneeded==3.4.5  # comment
    ...     # other==1.2.3
    ...     testlib>=5.6.7
    ...     
    ...     myApp # is great
    ...     git+https://github.com/USERNAME/REPONAME.git@BRANCH#egg=USERNAME
    ... '''.splitlines()))
    ('testlib>=5.6.7', 'myApp')
    """
    with _open(filename, 'rt') as filehandle:
        return tuple(filter(None, (
            REGEX_COMMENT.sub('', line).strip()
            for line in filehandle
        )))
