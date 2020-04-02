import contextlib, os
@contextlib.contextmanager
def preserve_cwd_context():
    # https://stackoverflow.com/a/169112/3356840
    curdir = os.getcwd()
    try: yield
    finally: os.chdir(curdir)


from functools import wraps
def preserve_cwd_decorator(_func):
    """
    >>> def test():
    ...     os.chdir('/')
    >>> curdir = os.getcwd()
    >>> test()
    >>> assert os.getcwd() != curdir
    >>> os.chdir(curdir)
    >>> assert os.getcwd() == curdir
    >>> test = preserve_cwd_decorator(test)
    >>> test()
    >>> assert os.getcwd() == curdir
    """
    assert callable(_func)
    @wraps(_func)
    def wrapper(*args, **kwargs):
        with preserve_cwd_context():
            return _func(*args, **kwargs)
    return wrapper
