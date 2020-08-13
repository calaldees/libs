import os
import re
import io
REGEX_COMMENT = re.compile(r'(?:\s*#(.*))|(git\+.*)')
def parse_requirements(filename, _open=io.open):
    """
    https://stackoverflow.com/a/16624700/3356840
    from pip.req import parse_requirements

    This is a backwards compatable python2 re-implementation

    This interpretation of `requirements.txt` is incomplete compared to the spec
    https://pip.pypa.io/en/stable/reference/pip_install/#example-requirements-file

    >>> def _mock_open(data):
    ...     class _mock_open_class():
    ...         def __init__(self, *args, **kwargs):
    ...             pass
    ...         def __enter__(self):
    ...             return data
    ...         def __exit__(self, type, value, traceback):
    ...             pass
    ...     return _mock_open_class
    >>> parse_requirements('test.txt', _mock_open('''#NOT A PACKAGE
    ...     # unneeded==3.4.5  # comment
    ...     # other==1.2.3
    ...     testlib>=5.6.7
    ...     
    ...     myApp # is great
    ...     git+https://github.com/USERNAME/REPONAME.git@BRANCH#egg=USERNAME
    ... '''.splitlines()))
    ('testlib>=5.6.7', 'myApp')
    """
    filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    with _open(filename, 'rt') as filehandle:
        return tuple(filter(None, (
            REGEX_COMMENT.sub('', line).strip()
            for line in filehandle
        )))

def parse_requirements_filter(filename, filter_packages=tuple()):
    return tuple(
        package
        for package in parse_requirements(filename)
        for filter_package in filter_packages
        if filter_package in package
    )
