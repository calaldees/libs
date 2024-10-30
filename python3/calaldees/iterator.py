from itertools import chain, zip_longest, filterfalse
from functools import partial, reduce

# TODO: Consider for inspriation
# WindowFixed, WindowSliding, Scan, Fold
# OpenJDK [JEP 473: Stream Gatherers (Second Preview)](https://openjdk.org/jeps/473)

def flatten(iterable):
    """
    https://docs.python.org/3/library/itertools.html#itertools-recipes

    >>> tuple(flatten(((1,2), (3,4))))
    (1, 2, 3, 4)
    """
    yield from chain.from_iterable(iterable)

def grouper(n, iterable, fillvalue=None):
    """
    https://stackoverflow.com/a/434411/3356840

    >>> tuple(grouper(3, 'ABCDEFG', 'x'))
    (('A', 'B', 'C'), ('D', 'E', 'F'), ('G', 'x', 'x'))
    """
    return zip_longest(*((iter(iterable),) * n), fillvalue=fillvalue)


# https://docs.python.org/3/library/itertools.html#itertools-recipes
def unique_everseen(iterable, key=None):
    "Yield unique elements, preserving order. Remember all elements ever seen."
    # unique_everseen('AAAABBBCCDAABBB') → A B C D
    # unique_everseen('ABBcCAD', str.casefold) → A B c D
    seen = set()
    if key is None:
        for element in filterfalse(seen.__contains__, iterable):
            seen.add(element)
            yield element
    else:
        for element in iterable:
            k = key(element)
            if k not in seen:
                seen.add(k)
                yield element


class IteratorCombine():
    r"""
    >>> i = IteratorCombine().map(lambda x: x+1).filter(lambda y: y>3)
    >>> tuple(i.process((1,2,3,4,5)))
    (4, 5, 6)
    >>> i = i.group(2)
    >>> tuple(i.process((1,2,3,4,5)))
    ((4, 5), (6, None))
    >>> i = i.flatten()
    >>> tuple(i.process((1,2,3,4,5)))
    (4, 5, 6, None)
    >>> i = i.unique()
    >>> tuple(i.process((1,2,3,4,4,5,5,1)))
    (4, 5, 6, None)

    >>> do_thing = IteratorCombine().map(partial(int.to_bytes, length=2, byteorder='big')).flatten().func(bytes).process
    >>> do_thing(b'abc')
    b'\x00a\x00b\x00c'

    # >>> def reducer(acc, item):
    # ...     acc += item
    # ...     return acc
    # >>> i = IteratorCombine().reduce(reducer)
    # >>> tuple(i.process((1,2,3,4,5)))

    """
    def __init__(self, operations=None):
        self._operations = operations or tuple()
    def func(self, func):
        return IteratorCombine(self._operations + (func,))
    def map(self, func):
        return self.func(partial(map, func))
    def filter(self, func):
        return self.func(partial(filter, func))
    def group(self, n):
        return self.func(partial(grouper, n))
    def flatten(self):
        return self.func(flatten)
    def unique(self):
        return self.func(unique_everseen)
    def reduction(self):
        raise NotImplementedError()
        return self.func()  # TODO: similar to `group`. It process multiple items and returns a single item.
    #def reduce(self, reducer, initializer=None):
    #    return self.func(partial(reduce, reducer, initializer=initializer))
    def process(self, data):
        return reduce(lambda iterable, func: func(iterable), self._operations, data)
