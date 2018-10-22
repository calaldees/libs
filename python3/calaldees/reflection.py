import inspect


def null_function(*args, **kwargs):
    pass


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


def funcname(level=1):
    """
    Use: print("My name is: %s" % inspect.stack()[0][3])
    >>> def test():
    ...     return funcname()
    >>> test()
    'test'
    """
    return inspect.stack()[level][3]
