from collections import namedtuple
import random


def baseconvert(number, fromdigits, todigits):
    """
    http://pastebin.com/f54dd69d6
    http://code.activestate.com/recipes/111286/?_ga=1.4032048.1464823167.1442695690
    http://code.activestate.com/recipes/410672-custom-string-representations-of-bases/

    converts a "number" between two bases of arbitrary digits

    The input number is assumed to be a string of digits from the
    fromdigits string (which is in order of smallest to largest
    digit). The return value is a string of elements from todigits
    (ordered in the same way). The input and output bases are
    determined from the lengths of the digit strings. Negative
    signs are passed through.

    decimal to binary
    >>> baseconvert(555, baseconvert.BASE10, baseconvert.BASE2)
    '1000101011'

    binary to decimal
    >>> baseconvert('1000101011', baseconvert.BASE2, baseconvert.BASE10)
    '555'

    integer interpreted as binary and converted to decimal (!)
    >>> baseconvert(1000101011, baseconvert.BASE2, baseconvert.BASE10)
    '555'

    base10 to base4
    >>> baseconvert(99, baseconvert.BASE10, "0123")
    '1203'

    base4 to base5 (with alphabetic digits)
    >>> baseconvert(1203, "0123", "abcde")
    'dee'

    base5, alpha digits back to base 10
    >>> baseconvert('dee', "abcde", baseconvert.BASE10)
    '99'

    decimal to a base that uses A-Z0-9a-z for its digits
    >>> baseconvert(257938572394, baseconvert.BASE10, baseconvert.BASE62)
    'E78Lxik'

    ..convert back
    >>> baseconvert('E78Lxik', baseconvert.BASE62, baseconvert.BASE10)
    '257938572394'

    binary to a base with words for digits (the function cannot convert this back)
    >>> baseconvert('1101', baseconvert.BASE2, ('Zero','One'))
    'OneOneZeroOne'

    """

    if str(number)[0] == '-':
        number = str(number)[1:]
        neg = 1
    else:
        neg = 0

    # make an integer out of the number
    x = 0
    for digit in str(number):
        x = x * len(fromdigits) + fromdigits.index(digit)

    # create the result in base 'len(todigits)'
    if x == 0:
        res = todigits[0]
    else:
        res = ""
        while x > 0:
            digit = x % len(todigits)
            res = todigits[digit] + res
            x = int(x / len(todigits))
        if neg:
            res = "-"+res

    return res

baseconvert.BASE2 = "01"
baseconvert.BASE10 = "0123456789"
baseconvert.BASE16 = "0123456789ABCDEF"
baseconvert.BASE36 = "0123456789abcdefghijklmnopqrstuvwxyz"
baseconvert.BASE62 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyz"


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

