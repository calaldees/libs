import traceback


def running_tests():
    """
    >>> running_tests()
    True
    """
    return any(_function_name for _, _, _function_name, _ in traceback.extract_stack() if 'test' in _function_name)
