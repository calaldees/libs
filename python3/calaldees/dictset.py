
def subdict(d, keys):
    return {k: v for k, v in d.items() if k in keys}

# Some of these can be superceeded by python3.9
#   https://peps.python.org/pep-0584/
# consider https://docs.python.org/3/library/functools.html#functools.total_ordering
# just __eq__ and __lt__
#@total_ordering
class DictSetOperationsMixin():
    """
    I was disappointed with pythons builtin support for set operations with dicts
    So I wrote this extension

    References
    https://www.python.org/dev/peps/pep-0584/
    https://github.com/arthurmoreno/setdict/blob/master/setdict/setdict.py
    https://www.geeksforgeeks.org/python-check-if-one-dictionary-is-subset-of-other/
    """
    def __and__(a, b):
        return {k: v for k, v in a.items() if b.get(k) == v} # DictSet?
    def __iand__(self, other):
        return DictSetOperationsMixin.__and__(self, other)

    def __or__(a, b):
        return DictSetOperationsMixin.__add__(a, b)
    def __ior__(self, other):
        return DictSetOperationsMixin.__iadd__(self, other)

    # TODO: was this added in python3.9 as `|` ??
    def __add__(a, b):
        return {**a, **b}  # TODO return DictSet?
    def __iadd__(self, other):
        self.update(other)
        return self

    def __le__(self, other):
        """
        >>> aa = DictSet({'a': 1, 'b': 2, 'c': 3})
        >>> bb = DictSet({'c': 3, 'd': 4, 'e': 5})
        >>> cc = DictSet({'a': 1})
        >>> aa <= cc
        False
        >>> cc <= aa
        True
        >>> aa <= aa
        True
        """
        return DictSetOperationsMixin.__ge__(other, self)
    def __lt__(self, other):
        return DictSetOperationsMixin.__le__(self, other) and (len(self) < len(other))
    def __ge__(self, other):
        """
        >>> DictSetOperationsMixin.__ge__(
        ...    {'a': None},
        ...    {'b': None},
        ... )
        False
        >>> DictSetOperationsMixin.__ge__(
        ...    {'a' : 1, 'b' : 2, 'c' : 3, 'd' : 4, 'e' : 5},
        ...    {'a' : 1, 'b' : 2, 'c' : 3},
        ... )
        True
        """
        return all(k in self and self[k] == v for k, v in other.items())
    def __gt__(self, other):
        """
        >>> aa = DictSet({'a': 1, 'b': 2, 'c': 3})
        >>> bb = DictSet({'c': 3, 'd': 4, 'e': 5})
        >>> cc = DictSet({'a': 1})
        >>> aa > cc
        True
        >>> cc > aa
        False
        """
        return DictSetOperationsMixin.__ge__(self, other) and (len(self) > len(other))


class DictSet(DictSetOperationsMixin, dict):
    pass
