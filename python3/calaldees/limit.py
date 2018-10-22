
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
