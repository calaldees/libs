import collections
from functools import reduce
from itertools import tee, zip_longest


def subdict(d, keys):
    return {k: v for k, v in d.items() if k in keys}


def list_neighbor_generator(_list, out_of_bounds_type=dict):
    """
    Todo - this is rubish - replace with zip()

    >>> ['{0}:{1}:{2}'.format(prev, current, next) for prev, current, next in list_neighbor_generator([1,2,3], out_of_bounds_type=str)]
    [':1:2', '1:2:3', '2:3:']
    """
    length = len(_list)
    for index, item in enumerate(_list):
        yield _list[index-1] if index > 0 else out_of_bounds_type(), item, _list[index+1] if index < length-1 else out_of_bounds_type()


def pairwise(iterable, fillvalue=None):
    """
    https://stackoverflow.com/a/5434936/3356840
    s -> (s0,s1), (s1,s2), (s2, s3), ...

    >>> tuple(pairwise((1,2,3)))
    ((1, 2), (2, 3), (3, None))
    """
    a, b = tee(iterable)
    next(b, None)
    return zip_longest(a, b, fillvalue=fillvalue)


def first(iterable):
    """
    Return the first non null value in an iterable

    TODO: tests
    """
    if not iterable:
        return None
    for i in iterable:
        if i:
            return i


def flatten(l):
    """
    http://stackoverflow.com/questions/2158395/flatten-an-irregular-list-of-lists-in-python

    >>> list(flatten([[[1, 2, 3], [4, 5]], 6]))
    [1, 2, 3, 4, 5, 6]
    """
    for el in l:
        if isinstance(el, collections.Iterable) and not isinstance(el, (str, bytes)):
            for sub in flatten(el):
                yield sub
        else:
            yield el


def duplicates(list_with_duplicates):
    """
    todo: tests
    """
    if not isinstance(list_with_duplicates, (list, tuple)):
        list_with_duplicates = tuple(list_with_duplicates)
    set_without_duplicates = set(list_with_duplicates)
    if len(set_without_duplicates) == len(list_with_duplicates):
        return []
    return [item for item in list_with_duplicates if not set_without_duplicates.pop(item)]


# https://stackoverflow.com/a/434411/3356840
from itertools import zip_longest
def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def freeze(items):
    """
    todo: tests
    """
    if isinstance(items, dict):
        items = items.items()
    if not isinstance(items, str) and hasattr(items, '__iter__'):
        return frozenset(freeze(item) for item in items)
    return items


def extract_subkeys(data, subkey):
    """
    >>> sorted(extract_subkeys({'a.a':1, 'a.b':2, 'b.a': 3}, 'a.').items())
    [('a', 1), ('b', 2)]
    """
    return {k.replace(subkey, ''): v for k, v in data.items() if k.startswith(subkey)}


def update_dict(dict_a, dict_b):
    """
    Because dict.update(d) does not return the new dict

    Updates dict_a with the contents of dict_b

    >>> a = {'a': 1, 'b': 2}
    >>> sorted(update_dict(a, {'b': 3, 'c': 3}).items())
    [('a', 1), ('b', 3), ('c', 3)]
    """
    dict_a.update(dict_b)
    return dict_a


def strip_non_base_types(d):
    """
    Recursively steps though a python dictionary
    Identifies strings and removes/replaces harmful/unwanted characters + collapses white space

    (The tests below rely on the dict ordering in the output, if pythons dict ordering changes this will break)

    >>> strip_non_base_types('a')
    'a'

    ## Cant reply on dict order between versions of python
    ##>>> strip_non_base_types({'a':1, 'b':'2', 'c':[3,4,5], 'd':{'e':'6'}})
    ##{'a': 1, 'c': [3, 4, 5], 'b': '2', 'd': {'e': '6'}}
    ##>>> strip_non_base_types({'a':1, 'b':'2', 'c':[3,4,5], 'd':{'e':datetime.datetime.now()}})
    ##{'a': 1, 'c': [3, 4, 5], 'b': '2', 'd': {'e': None}}

    """
    for t in [str, int, float, bool]:
        if isinstance(d, t):
            return d
    if hasattr(d, 'items'):
        return {key: strip_non_base_types(value) for key, value in d.items()}
    for t in [list, set, tuple]:
        if isinstance(d, t):
            return [strip_non_base_types(v) for v in d]
    return None


#http://stackoverflow.com/questions/4126348/how-do-i-rewrite-this-function-to-implement-ordereddict/4127426#4127426
class OrderedDefaultdict(collections.OrderedDict):
    def __init__(self, *args, **kwargs):
        if not args:
            self.default_factory = None
        else:
            if not (args[0] is None or callable(args[0])):
                raise TypeError('first argument must be callable or None')
            self.default_factory = args[0]
            args = args[1:]
        super(OrderedDefaultdict, self).__init__(*args, **kwargs)

    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        self[key] = default = self.default_factory()
        return default

    def __reduce__(self):  # optional, for pickle support
        args = self.default_factory if self.default_factory else tuple()
        return type(self), args, None, None, self.items()

    def last(self):
        return reversed(self).__next__()


def defaultdict_recursive():
    return collections.defaultdict(defaultdict_recursive)


def merge_dicts(*args, _allow_merge_condition_function=lambda v: v):
    """
    merge_dicts - with function to marshal the merging of a key
    merge single level

    This was created to prevent merging of dicts where the value of the key was 'None'

    >>> merge_dicts({'a': 1, 'b': 2, 'c': None}, {'a': 5, 'b': None, 'c': 3, 'd': 4})
    {'a': 5, 'b': 2, 'c': 3, 'd': 4}
    """
    def _merge_dicts(accumulator, i):
        for k, v in i.items():
            if (k in accumulator and _allow_merge_condition_function(v)) or (k not in accumulator):
                accumulator[k] = v
        return accumulator
    return reduce(_merge_dicts, args, {})
