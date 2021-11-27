import collections
from functools import reduce, partial
from itertools import tee, zip_longest, cycle, chain


def get_keys(obj):
    if hasattr(obj, 'keys'):
        return obj.keys()
    elif hasattr(obj, '__dict__'):
        return vars(obj).keys()
    return set()
def get_attr_or_item(obj, field):
    try:
        return obj[field]
    except:
        return getattr(obj, field)
def set_attr_or_item(obj, field, value):
    try:
        obj[field] = value
    except TypeError:
        setattr(obj, field, value)
def set_attr_or_item_all(source, target):
    for field in get_keys(source):
        set_attr_or_item(target, field, get_attr_or_item(source, field))

# Depricate in preference to DictSet?
def subdict(d, keys):
    return {k: v for k, v in d.items() if k in keys}

def list_neighbor_generator(_list, out_of_bounds_type=dict):
    """
    Todo - this is rubish - replace with zip()
    TODO: see cycle_offset() below

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

def pairwise_inverse(iterable, fillvalue=None):
    """
    >>> tuple(pairwise_inverse((1,2,3)))
    ((None, 1), (1, 2), (2, 3))
    """
    a, b = tee(iterable)
    a = chain((fillvalue, ), a)
    return zip(a, b)

def is_last(iterable):
    """
    >>> tuple(is_last('123'))
    (('1', False), ('2', False), ('3', True))
    """
    return ((a, True if b is None else False) for a, b in pairwise(iterable))
def is_first(iterable):
    """
    >>> tuple(is_first('123'))
    (('1', True), ('2', False), ('3', False))
    """
    return ((b, True if a is None else False) for a, b in pairwise_inverse(iterable))

def cycle_offset(iterator, offset=0, yield_values=1, num_yields=None):
    """
    >>> tuple(cycle_offset((1,2,3,4,5)))
    (1, 2, 3, 4, 5)
    >>> tuple(cycle_offset((1,2,3,4,5), offset=2))
    (3, 4, 5, 1, 2)
    >>> tuple(cycle_offset((1,2,3,4,5), offset=0, yield_values=2))
    ((1, 2), (2, 3), (3, 4), (4, 5), (5, 1))
    >>> tuple(cycle_offset((1,2,3,4,5), offset=-1, yield_values=3))
    ((5, 1, 2), (1, 2, 3), (2, 3, 4), (3, 4, 5), (4, 5, 1))
    >>> tuple(cycle_offset((1,2,3,4,5), num_yields=2))
    (1, 2)
    >>> tuple(cycle_offset((1,2,3,4,5), num_yields=6))
    (1, 2, 3, 4, 5, 1)
    """
    original_length = len(iterator)
    num_yields = num_yields if isinstance(num_yields, int) else original_length
    iterators = tuple(cycle(_iterator) for _iterator in tee(iterator, yield_values))
    for _iterator_index, _iterator in enumerate(iterators):
        _offset = offset + _iterator_index
        if _offset < 0:
            _offset += original_length
        for _ in range(_offset):
            next(_iterator)
    for _ in range(num_yields):
        if len(iterators) == 1:
            yield next(iterators[0])
        else:
            yield tuple(next(_iterator) for _iterator in iterators)


def _blend_mix_func(a, b, blend=0.5):
    assert 0 <= blend <= 1
    return (a * (1-blend)) + (b * (blend))
def blend(a, b, target=None, blend=0.5):
    """
    Blends two objects or dicts

    Dict order is not predicatble for doctest - so I have use '=='

    >>> blend({'a': 50}, {'a': 100}, blend=0)
    {'a': 50}
    >>> blend({'a': 50}, {'a': 100}, blend=0.5)
    {'a': 75.0}
    >>> class TestObj():
    ...    def __init__(self, a=0):
    ...        self.a = a
    >>> test_obj = TestObj()
    >>> blend({'a': 50}, {'a': 100}, target=test_obj, blend=0.25).a
    62.5
    >>> color_1 = {'red': 1.0, 'green': 0.5, 'blue': 1.0}
    >>> color_2 = {'red': 0.0, 'green': 0.5, 'blue': 0.5}
    >>> blend(color_1, color_2, blend=0.5) == {'red': 0.5, 'green': 0.5, 'blue': 0.75}
    True
    >>> blend(color_1, color_2, blend=0.0) == {'red': 1.0, 'green': 0.5, 'blue': 1.0}
    True
    >>> blend(color_1, color_2, blend=1.0) == {'red': 0.0, 'green': 0.5, 'blue': 0.5}
    True
    >>> blend(1, 2, 0.5)
    1.5
    """
    return mix(a, b, target=target, mix_func=partial(_blend_mix_func, blend=blend))
def mix(a, b, *, target=None, mix_func=None):
    """
    """
    assert callable(mix_func)
    target = target or {}
    fields = get_keys(a) & get_keys(b)
    if fields:
        for field in fields:
            value = mix_func(get_attr_or_item(a, field), get_attr_or_item(b, field))
            set_attr_or_item(target, field, value)
        return target
    return mix_func(a, b)



def get_index_float(index, array):
    """
    >>> array = (0,1,2,3,4,5,6,7,8,9)
    >>> get_index_float(0.00, array)
    0
    >>> get_index_float(0.50, array)
    5
    >>> get_index_float(0.55, array)
    5
    >>> get_index_float(0.59, array)
    5
    >>> get_index_float(0.60, array)
    6
    >>> get_index_float(0.99, array)
    9
    >>> get_index_float(1.00, array)
    9
    """
    assert 0 <= index <= 1
    return array[min(len(array)-1, int(index * len(array)))]


def get_index_float_blend(index_float, array):
    """
    >>> get_index_float_blend(1.5, (1,2,3))
    2.5
    >>> get_index_float_blend(3.5, (1,2,3))
    1.5
    >>> get_index_float_blend(0.5, ({'a': 1},{'a': 2},{'a': 3}))
    {'a': 1.5}
    """
    index = int(index_float)
    a = array[(index) % len(array)]
    b = array[(index+1) % len(array)]
    return blend(a, b, blend=index_float % 1)


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


def isiterable(iterable):
    """
    https://stackoverflow.com/a/36407550/3356840

    Alternate:
    if isinstance(item, collections.abc.Iterable) and not isinstance(item, str):
    """
    if isinstance(iterable, (str, bytes)):
        return False
    try:
        _ = iter(iterable)
    except TypeError:
        return False
    else:
        return True


def flatten(*args, dict_values=True):
    """
    http://stackoverflow.com/questions/2158395/flatten-an-irregular-list-of-lists-in-python

    >>> tuple(flatten([[[1, 2, 3], ['4', 5]], 6], 7, '8'))
    (1, 2, 3, '4', 5, 6, 7, '8')
    >>> tuple(flatten((1, {'b':2, 'c': 3})))
    (1, 2, 3)
    >>> tuple(flatten((1, {'b':2, 'c': 3}), dict_values=False))
    (1, 'b', 'c')
    """
    for iterable in args:
        if isiterable(iterable):
            for item in iterable:
                if isiterable(item):
                    if dict_values and isinstance(item, collections.abc.Mapping):
                        yield from item.values()
                    else:
                        yield from flatten(item)
                else:
                    yield item
        else:
            yield iterable


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


def grouper(iterable, n, fillvalue=None):
    """
    https://stackoverflow.com/a/434411/3356840

    >>> tuple(grouper('ABCDEFG', 3, 'x'))
    (('A', 'B', 'C'), ('D', 'E', 'F'), ('G', 'x', 'x'))
    """
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


# python 3.9 now supports `+=` for dicts
# Remove this?
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
