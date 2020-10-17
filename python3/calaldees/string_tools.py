from collections import namedtuple
import random


TextOverlap = namedtuple('TextOverlap', ('index', 'text'))
def commonOverlap(text1, text2):
    """
    https://neil.fraser.name/news/2010/11/04/

    >>> commonOverlap('Fire at Will', 'William Riker is number one')
    TextOverlap(index=4, text='Will')
    >>> commonOverlap('Have some CoCo and CoCo', 'CoCo and CoCo is here.')
    TextOverlap(index=13, text='CoCo and CoCo')

    """
    index = min(len(text1), len(text2))
    while index > 0:
        if text1[-index:] == text2[:index]:
            break
        index -= 1
    return TextOverlap(index, text2[:index])


def random_string(length=8):
    """
    Generate a random string of a-z A-Z 0-9
    (Without vowels to stop bad words from being generated!)

    >>> len(random_string())
    8
    >>> len(random_string(10))
    10

    If random, it should compress pretty badly:

    >>> import zlib
    >>> len(zlib.compress(random_string(100).encode('utf-8'))) > 50
    True
    """
    random_symbols = '1234567890bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ'
    r = ''
    for i in range(length):
        r += random_symbols[random.randint(0, len(random_symbols)-1)]
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
    # todo? from typing import Iterable ; if isinstance(my_item, Iterable):  or collections.Iterable
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

