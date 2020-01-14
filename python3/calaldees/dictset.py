
def subdict(d, keys):
    return {k: v for k, v in d.items() if k in keys}

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
        ...    {'gfg' : 1, 'is' : 2, 'best' : 3, 'for' : 4, 'CS' : 5},
        ...    {'gfg' : 1, 'is' : 2, 'best' : 3},
        ... )
        True
        """
        return all(self.get(k, None) == v for k, v in other.items())
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
