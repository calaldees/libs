from itertools import chain, zip_longest
from types import MappingProxyType
from functools import partial, reduce

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

class IteratorCombine():
    """
    >>> i = IteratorCombine().map(lambda x: x+1).filter(lambda y: y>3)
    >>> tuple(i.iterator((1,2,3,4,5)))
    (4, 5, 6)
    >>> i = i.group(2)
    >>> tuple(i.iterator((1,2,3,4,5)))
    ((4, 5), (6, None))
    >>> i = i.flatten()
    >>> tuple(i.iterator((1,2,3,4,5)))
    (4, 5, 6, None)
    """
    def __init__(self, operations=None):
        self._operations = operations or tuple()
    def map(self, func):
        return IteratorCombine(self._operations + (partial(map, func),))
    def filter(self, func):
        return IteratorCombine(self._operations + (partial(filter, func),))
    def group(self, n):
        return IteratorCombine(self._operations + (partial(grouper, n),))
    def flatten(self):
        return IteratorCombine(self._operations + (flatten,))
    def reduction(self):
        raise NotImplementedError()
        return IteratorCombine(self._operations)
    def iterator(self, data):
        return reduce(lambda iterable, func: func(iterable), self._operations, data)
